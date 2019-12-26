# This script gets all of the relevant project metrics from a list
# of usernames. It can easily be adapted to get metrics from project ids
# or slugs by not calling get_projects() and iterating through the ids/slugs
# instead. Metrics are obtained using the ghtorrent server and the GitHub API.
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
from datetime import datetime
import stscraper
import stutils
from multiprocessing import Pool
import mysql.connector
import os
from git import Repo
import json

urls = ['https://api.github.com/repos/', 'https://api./repos/']
df_data = pd.read_csv('files/20190709_reverse_dependency_counts.csv')
# Get list of project_ids and urls associated with username
def get_projects(username, db):
    try:
        d_projects = pd.read_sql("""select p.id, p.url from `ghtorrent-2018-03`.projects p,
            `ghtorrent-2018-03`.users u where p.owner_id = u.id and u.login = '%s';"""
            % username, con=db)
        if d_projects.empty:
            return None
        else:
            # remove duplicate rows
            d_projects = d_projects.drop_duplicates()
            # remove rows with duplicate project_ids
            grouped_id = d_projects.groupby('id')
            df_new = pd.DataFrame(columns=['id', 'url'])
            for id, df_id in grouped_id:
                if df_id.shape[0] == 1:
                    df_new = df_new.append(df_id, ignore_index=True, sort=False)
            return df_new
    except:
        return None

# get number of core contributors, which are number of contributors that together
# make up more than 80% of commits
def get_num_core(id, db, num_commits):
    # get data on committer id and number of commits
    d_core = pd.read_sql("""select distinct commits.committer_id as 'committer_id', count(*) as 'num_commits' from commits where commits.project_id = '%i' group by committer_id order by num_commits desc;""" % id,
            con=db)
    # iterate through num_commmits column and keep incrementing counter until sum of commits is > that 0.8*num_commits
    num_core = 0
    counter = 0
    threshold = num_commits*0.8
    for commits in d_core['num_commits'].values:
        num_core += commits
        counter += 1
        if num_core > threshold:
            return counter
    return 0

def get_download(id, db):
    try:
        df_data = pd.read_sql("""select sum(d.downloads) as 'num_download'
            from badges.funding_downloads d,
            `ghtorrent-2018-03`.projects p where d.name = p.name and p.id = '%i';"""
                % id, con=db)
        if df_data.empty:
            raise
        # Get the sum of the downloads column
        return df_data['num_download'].values[0]
    except:
        return None

# get info on commits, stars, and issues
def get_info(id, db): # can be changed to slug
    # Get project_id if not already known
    # (id, forked_from) = get_id(slug, db)
    #
    # if id is None:
    #     return None
    df_forked = pd.read_sql("""select forked_from from projects where id = '%i';""" % id,
            con=db)
    if df_forked.empty or df_forked.shape[0] > 1:
        # Nothing for that project found
        return (None, None)
    else:
        forked_from = df_forked.forked_from
    # Get total number of committers
    d_committer_total = pd.read_sql("""select count(distinct c.author_id)
        as 'num_committer_total' from commits c where c.project_id = '%i';""" % id,
            con=db)
    # Get total number of commits
    d_commit_total = pd.read_sql("""select count(*) as 'num_commit_total' from commits c where c.project_id = '%i';""" % id,
            con=db)
    num_commits = d_commit_total.num_commit_total.values[0]
    num_core = get_num_core(id, db, num_commits)
    num_download = get_download(id, db)
    d_committer_total['project_id'] = id
    d_committer_total['num_core'] = num_core
    d_committer_total['forked_from'] = forked_from
    if num_download is None:
        d_committer_total['num_download'] = np.nan
    else:
        d_committer_total['num_download'] = num_download
    # Get number of committers from 8/23/18 to 5/23/19
    d_committer = pd.read_sql("""select count(distinct c.author_id)
        as 'num_committer' from commits c where c.project_id = '%i' and c.created_at >= '2018-08-23'
        and c.created_at <= '2019-05-23';""" % id,
            con=db)
    # Get total number of stars
    d_star_total = pd.read_sql("""select count(*) as 'num_star_GHT' from watchers w where w.repo_id = '%i';""" % id,
            con=db)
    # Get date of first commit
    d_date = pd.read_sql("""select c.created_at as 'first_commit_date' from commits c where
        c.project_id = '%i' order by first_commit_date asc limit 1;""" % id,
            con=db)
    if not d_date.empty:
        # Get age
        today = datetime.now()
        time = d_date['first_commit_date'].values[0]
        time = datetime.utcfromtimestamp(time.tolist()/1e9)
        d_date['age'] = (today - time).days
    elif num_commits == 0:
        d_date['first_commit_date'] = np.nan
        d_date['age'] = np.nan
    else:
        print(id)
        return None
    # Get total number of issues
    d_issue_total = pd.read_sql("""select count(distinct i.id) as 'num_issue_total' from issues i
        where i.repo_id = '%i' and i.pull_request_id is NULL;""" % id,
            con=db)
    # Get number of issues from 8/23/18 to 5/23/19
    d_issue = pd.read_sql("""select count(distinct i.id) as 'num_issue' from issues i where i.repo_id = '%i'
        and i.pull_request_id is NULL and i.created_at >= '2018-08-23' and i.created_at <= '2019-05-23';""" % id,
            con=db)
    # Get total number of closed issues
    d_closed_total = pd.read_sql("""select count(distinct e.issue_id) as 'num_closed_total' from issues i,
        issue_events e where i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
        and e.action ='closed';""" % id,
            con=db)
    # Get number of closed issues from 8/23/18 to 5/23/19
    d_closed = pd.read_sql("""select count(distinct e.issue_id) as 'num_closed' from issues i,
        issue_events e where i.repo_id = '%i' and i.pull_request_id is NULL and
        i.id = e.issue_id and e.action ='closed' and e.created_at >= '2018-08-23' and
        e.created_at <= '2019-05-23';""" % id,
            con=db)
    # Get total number of pull requests
    d_pr_total = pd.read_sql("""select count(distinct i.id) as 'num_pr_total' from issues i
        where i.repo_id = '%i' and i.pull_request_id is not NULL;""" % id,
            con=db)
    # Get number of pull requests from 8/23/18 to 5/23/19
    d_pr = pd.read_sql("""select count(distinct i.id) as 'num_pr' from issues i
        where i.repo_id = '%i' and i.pull_request_id is not NULL and i.created_at >= '2018-08-23'
        and i.created_at <= '2019-05-23';""" % id,
            con=db)
    # Get organization and company involvement
    d_org = pd.read_sql("""select u.type as 'project_type' from projects p, users u where
        p.id = '%i' and p.owner_id = u.id;""" % id, con=db)
    # Get total number of external issues
    d_external_total = pd.read_sql("""select count(distinct i.id) as 'num_external_total' from issues i where i.reporter_id not in
        (select distinct e.actor_id as 'internal_id' from issues i, issue_events e where i.repo_id = '%i' and e.action = 'closed' and
        i.id = e.issue_id and e.actor_id <> i.reporter_id) and i.repo_id = '%i' and
        i.pull_request_id is NULL;""" % (id,id), con=db)
    # Get number of external issues from 8/23/18 to 5/23/19
    d_external = pd.read_sql("""select count(distinct i.id) as 'num_external' from issues i where i.reporter_id not in
        (select distinct e.actor_id as 'internal_id' from issues i, issue_events e where i.repo_id = '%i' and e.action = 'closed' and
        i.id = e.issue_id and e.actor_id <> i.reporter_id) and i.repo_id = '%i' and
        i.pull_request_id is NULL and i.created_at >= '2018-08-23' and i.created_at <= '2019-05-23';""" % (id,id), con=db)
    # Merge the dataframes
    d = pd.concat([d_committer, d_committer_total, d_star_total, d_date, d_issue, d_issue_total,
        d_closed, d_closed_total, d_external, d_external_total, d_pr, d_pr_total, d_org], axis=1, sort=False)
    return d

def get_name(id, db):
    df_name = pd.read_sql("""select p.name from `ghtorrent-2018-03`.projects p
        where p.id = '%i';""" % id, con=db)

    if df_name.empty or df_name.shape[0] > 1:
        return None
    else:
        return df_name['name'].values[0]

def get_count(id, db):
    name = get_name(id, db)
    if name is None:
        return None

    df_sub = df_data[df_data.name==name]

    if df_sub.empty:
        return 0
    elif df_sub.shape[0] > 1:
        print(id, name)
        return None

    return df_sub.reverse_dependency_count.values[0]

def get_metrics(pair):
    (id, url) = pair
    slug = '/'.join(url.split('/')[-2:])
    if error is not None:
        return (None, slug)
    # Get query metrics
    # Create a connection object
    db = mysql.connector.connect(host='localhost', user='', passwd='', database='ghtorrent-2018-03')
    # Create a cursor object to interact with the server
    cur = db.cursor()
    df = get_info(id, db)
    if df is None:
        return (None, slug)
    # Get reverse_dependency_count
    count = get_count(id, db)
    if count is None:
        df['reverse_dependency_count'] = np.nan
    else:
        df['reverse_dependency_count'] = count
    df['size'] = size
    df['slug'] = slug
    df = df[['project_id', 'slug', 'forked_from',
        'num_core', 'num_committer',
        'num_committer_total', 'num_star_GHT', 'num_download',
        'reverse_dependency_count', 'first_commit_date', 'age', 'num_issue',
        'num_issue_total', 'num_closed', 'num_closed_total', 'num_external',
        'num_external_total', 'num_pr', 'num_pr_total', 'project_type', 'size']]
    return (df, None)

# Get the num_commit (from 8/23/18 to 5/23/19) and num_commit_total
def get_commit_info(api, slug):
    num_commit_total = 0
    num_commit = 0
    upper_date = datetime(2019, 5, 23)
    lower_date = datetime(2018, 8, 23)
    commits = api.repo_commits(slug)
    for commit in commits:
        commit_date = convert_datetime(commit['commit']['author']['date'])
        if commit_date <= upper_date:
            num_commit_total += 1
            if commit_date >= lower_date:
                num_commit += 1
    return (num_commit_total, num_commit)

# Use github api to get some metrics
def get_api_info(api, slug):
    dict = {}
    try:
        repo = api.repo_info(slug)
        dict['num_star_GH'] = repo['stargazers_count']
        dict['size_GH'] = repo['size']
        dict['fork'] = repo['forks_count']
        dict['license'] = repo['license']
        dict['default_branch'] = repo['default_branch']
        dict['is_fork'] = repo['fork']
        dict['created_at'] = repo['created_at']
        dict['updated_at'] = repo['updated_at']
        dict['language'] = repo['language']
        dict['slug'] = slug
        (num_commit_total, num_commit) = get_commit_info(api, slug)
        dict['num_commit_total'] = num_commit_total
        dict['num_commit'] = num_commit
        return (dict, None)
    except:
        return (None, slug)

if __name__ == "__main__":
    # Input GitHub API tokens (in one string, separated by commas)
    stutils.CONFIG['GITHUB_API_TOKENS'] = ''
    api = stscraper.GitHubAPI()

    # Open CSV file with usernames (or project ids or slugs)
    df_username = pd.read_csv('insert file name')
    usernames = df_username['owner_username'].values

    df_metrics = pd.DataFrame(columns=['project_id', 'slug', 'forked_from', 'fork', 'is_fork', 'license', 'default_branch',
        'language', 'created_at', 'updated_at', 'num_core', 'num_commit', 'num_committer',
        'num_commit_total', 'num_committer_total', 'num_star_GHT', 'num_star_GH', 'num_download',
        'reverse_dependency_count', 'first_commit_date', 'age', 'num_issue',
        'num_issue_total', 'num_closed', 'num_closed_total', 'num_external',
        'num_external_total', 'num_pr', 'num_pr_total', 'project_type', 'size', 'size_GH'])

    # Create a connection object
    db = mysql.connector.connect(host='localhost', user='', passwd='', database='ghtorrent-2018-03')
    # Create a cursor object to interact with the server
    cur = db.cursor()

    pool = Pool(processes=8)

    errors = []

    for username in usernames[:]:
        df1 = pd.DataFrame(columns=['project_id', 'slug', 'forked_from',
            'num_core', 'num_committer',
            'num_committer_total', 'num_star_GHT', 'num_download',
            'reverse_dependency_count', 'first_commit_date', 'age', 'num_issue',
            'num_issue_total', 'num_closed', 'num_closed_total', 'num_external',
            'num_external_total', 'num_pr', 'num_pr_total', 'project_type', 'size'])
        df2 = pd.DataFrame(columns = ['slug', 'num_commit', 'num_commit_total'
                'num_star_GH', 'size_GH', 'fork', 'is_fork', 'license', 'default_branch',
                'language', 'created_at', 'updated_at'])
        df_project = get_projects(username, db)
        if df_project is not None:
            # Go through projects and get metrics
            pairs = list(set(zip(df_project.id, df_project.url)))
            for result in pool.imap_unordered(get_metrics, tqdm(pairs[:])):
                (df_temp1, error) = result
                if error is not None:
                    errors.append(error)
                else:
                    df1 = df1.append(df_temp1, ignore_index=True, sort=False)

            for pair in tqdm(pairs[:]):
                (dict, error) = get_api_info(api, pair)
                if error is not None:
                    errors.append(error)
                else:
                    dict['license'] = str(dict['license'])
                    df2 = df2.append(dict, ignore_index=True, sort=False)
            # Merge df1 and df2
            df_merged = df1.merge(df2, on='slug', suffixes=(False, False)).drop_duplicates()
            df_metrics = df_metrics.append(df_merged, ignore_index=True, sort=False)

    df_metrics.to_csv('insert file name', index=False)
    pd.Series(errors, name='error').to_csv('insert file name', header=True, index=False)
