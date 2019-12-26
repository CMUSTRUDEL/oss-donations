# This script gets the raw monthly data used in RDD from the ghtorrent server
import mysql.connector
import json
import pandas as pd
import time
from multiprocessing import Pool
from tqdm import tqdm
from datetime import datetime, timedelta
import numpy as np

# Get list of relevant projects with their project ids
df_metric = pd.read_csv('files/20190727_asking_all.csv')

# Convert string to datetime object
def convert_datetime(x):
    if not isinstance(x, str):
        return x
    # Ignore time zone info
    if 'T' in x and 'Z' in x:
        x = x.split('T')[0]
    try:
        return datetime.strptime(x, '%Y-%m-%d')
    except:
        try:
            return datetime.strptime(x, '%m/%d/%Y')
        except:
            try:
                return datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
            except:
                return datetime.strptime(x, '%m/%d/%Y %H:%M')

def clean_timedelta(x):
    return x.total_seconds() / timedelta(days=1).total_seconds()

# Return array of datetimes that represent the date boundaries to use
# when getting month data
def get_boundaries(intro_time):
    # convert intro_time to datetime
    intro_time = convert_datetime(intro_time)
    # create 30-day buffer window around funding adoption
    intro_left = intro_time - timedelta(days=15)
    intro_right = intro_time + timedelta(days=15)
    # compute boundaries of panel intervals
    num_window = 9
    delta = 30
    boundaries = [intro_left - i * timedelta(days=delta) for i in range(num_window, 0, -1)]
    boundaries += [intro_left, intro_right]
    boundaries += [intro_right + i * timedelta(days=delta) for i in range(1, num_window+1, 1)]
    return boundaries

# Run queries for a single time range
def get_month_data(start, end, project_id, index, slug, db):
    if index < 9:
        d_commit = pd.read_sql("""select count(*) as 'num_commit' from `ghtorrent-2018-03`.commits
                c where c.project_id = '%i' and c.created_at >= '%s' and
                c.created_at < '%s';""" % (project_id, start, end), con=db)
        d_closed = pd.read_sql("""select count(distinct e.issue_id) as 'num_closed'
                from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
                where i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
                and e.action='closed' and e.created_at >= '%s' and
                e.created_at < '%s';""" % (project_id, start, end),
                con=db)
        d_closed_external = pd.read_sql("""select count(distinct i.id) as 'num_closed_external'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
            where i.reporter_id not in (select distinct e.actor_id as 'internal_id'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e where
            i.repo_id = '%i' and e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and
            i.id = e.issue_id and e.action ='closed' and e.created_at >= '%s'
            and e.created_at < '%s';""" % (project_id, project_id, start, end), con=db)
        d_closed_internal = pd.read_sql("""select count(distinct i.id) as 'num_closed_internal'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
            where i.reporter_id in (select distinct e.actor_id as 'internal_id'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e where
            i.repo_id = '%i' and e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and
            i.id = e.issue_id and e.action ='closed' and e.created_at >= '%s'
            and e.created_at < '%s';""" % (project_id, project_id, start, end), con=db)
        d_closed_pr = pd.read_sql("""select count(distinct p.pull_request_id) as
            'num_closed_pr' from `ghtorrent-2018-03`.pull_request_history p,
            `ghtorrent-2018-03`.issues i where i.repo_id = '%i' and
            i.pull_request_id is not NULL and i.pull_request_id = p.pull_request_id
            and p.action ='closed' and p.created_at >= '%s' and p.created_at < '%s';"""
            % (project_id, start, end), con=db)
        # Get open and close times
        d_closed_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            i.pull_request_id is NULL and i.id = e.issue_id and e.action ='closed'
            and e.created_at >= '%s' and e.created_at < '%s';"""
            % (project_id, start, end), con=db)
        d_closed_external_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.reporter_id not in
            (select distinct e.actor_id as 'internal_id' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
            and e.action ='closed' and e.created_at >= '%s' and e.created_at < '%s';"""
            % (project_id, project_id, start, end), con=db)
        d_closed_internal_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.reporter_id in
            (select distinct e.actor_id as 'internal_id' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
            and e.action ='closed' and e.created_at >= '%s' and e.created_at < '%s';"""
            % (project_id, project_id, start, end), con=db)
        d_closed_pr_time = pd.read_sql("""select i.id, i.pull_request_id as 'issue_id', i.created_at as 'open_time',
            p.created_at as 'close_time' from `ghtorrent-2018-03`.pull_request_history p,
            `ghtorrent-2018-03`.issues i where i.repo_id = '%i' and i.pull_request_id
            is not NULL and i.pull_request_id = p.pull_request_id and p.action ='closed'
            and p.created_at >= '%s' and p.created_at < '%s';"""
            % (project_id, start, end), con=db)
    elif index==9:
        d_commit = pd.read_sql("""select count(*) as 'num_commit' from commits c where c.project_id = '%i'
                and c.created_at >= '%s' and c.created_at <= '%s';""" % (project_id, start, end),
                con=db)
        d_closed = pd.read_sql("""select count(distinct e.issue_id) as 'num_closed'
                from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
                where i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
                and e.action='closed' and e.created_at >= '%s' and
                e.created_at <= '%s';""" % (project_id, start, end),
                con=db)
        d_closed_external = pd.read_sql("""select count(distinct i.id) as 'num_closed_external'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
            where i.reporter_id not in (select distinct e.actor_id as 'internal_id'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e where
            i.repo_id = '%i' and e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and
            i.id = e.issue_id and e.action ='closed' and e.created_at >= '%s'
            and e.created_at <= '%s';""" % (project_id, project_id, start, end), con=db)
        d_closed_internal = pd.read_sql("""select count(distinct i.id) as 'num_closed_internal'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
            where i.reporter_id in (select distinct e.actor_id as 'internal_id'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e where
            i.repo_id = '%i' and e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and
            i.id = e.issue_id and e.action ='closed' and e.created_at >= '%s'
            and e.created_at <= '%s';""" % (project_id, project_id, start, end), con=db)
        d_closed_pr = pd.read_sql("""select count(distinct p.pull_request_id) as
            'num_closed_pr' from `ghtorrent-2018-03`.pull_request_history p,
            `ghtorrent-2018-03`.issues i where i.repo_id = '%i' and
            i.pull_request_id is not NULL and i.pull_request_id = p.pull_request_id
            and p.action ='closed' and p.created_at >= '%s' and p.created_at <= '%s';"""
            % (project_id, start, end), con=db)
        # Get open and close times
        d_closed_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            i.pull_request_id is NULL and i.id = e.issue_id and e.action ='closed'
            and e.created_at >= '%s' and e.created_at <= '%s';"""
            % (project_id, start, end), con=db)
        d_closed_external_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.reporter_id not in
            (select distinct e.actor_id as 'internal_id' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
            and e.action ='closed' and e.created_at >= '%s' and e.created_at <= '%s';"""
            % (project_id, project_id, start, end), con=db)
        d_closed_internal_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.reporter_id in
            (select distinct e.actor_id as 'internal_id' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
            and e.action ='closed' and e.created_at >= '%s' and e.created_at <= '%s';"""
            % (project_id, project_id, start, end), con=db)
        d_closed_pr_time = pd.read_sql("""select i.id, i.pull_request_id as 'issue_id', i.created_at as 'open_time',
            p.created_at as 'close_time' from `ghtorrent-2018-03`.pull_request_history p,
            `ghtorrent-2018-03`.issues i where i.repo_id = '%i' and i.pull_request_id
            is not NULL and i.pull_request_id = p.pull_request_id and p.action ='closed'
            and p.created_at >= '%s' and p.created_at <= '%s';"""
            % (project_id, start, end), con=db)
    else:
        d_commit = pd.read_sql("""select count(*) as 'num_commit' from commits c where c.project_id = '%i'
                and c.created_at > '%s' and c.created_at <= '%s';""" % (project_id, start, end),
                con=db)
        d_closed = pd.read_sql("""select count(distinct e.issue_id) as 'num_closed'
                from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
                where i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
                and e.action='closed' and e.created_at > '%s' and
                e.created_at <= '%s';""" % (project_id, start, end),
                con=db)
        d_closed_external = pd.read_sql("""select count(distinct i.id) as 'num_closed_external'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
            where i.reporter_id not in (select distinct e.actor_id as 'internal_id'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e where
            i.repo_id = '%i' and e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and
            i.id = e.issue_id and e.action ='closed' and e.created_at > '%s'
            and e.created_at <= '%s';""" % (project_id, project_id, start, end), con=db)
        d_closed_internal = pd.read_sql("""select count(distinct i.id) as 'num_closed_internal'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e
            where i.reporter_id in (select distinct e.actor_id as 'internal_id'
            from `ghtorrent-2018-03`.issues i, `ghtorrent-2018-03`.issue_events e where
            i.repo_id = '%i' and e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and
            i.id = e.issue_id and e.action ='closed' and e.created_at > '%s'
            and e.created_at <= '%s';""" % (project_id, project_id, start, end), con=db)
        d_closed_pr = pd.read_sql("""select count(distinct p.pull_request_id) as
            'num_closed_pr' from `ghtorrent-2018-03`.pull_request_history p,
            `ghtorrent-2018-03`.issues i where i.repo_id = '%i' and
            i.pull_request_id is not NULL and i.pull_request_id = p.pull_request_id
            and p.action ='closed' and p.created_at > '%s' and p.created_at <= '%s';"""
            % (project_id, start, end), con=db)
        # Get open and close times
        d_closed_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            i.pull_request_id is NULL and i.id = e.issue_id and e.action ='closed'
            and e.created_at > '%s' and e.created_at <= '%s';"""
            % (project_id, start, end), con=db)
        d_closed_external_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.reporter_id not in
            (select distinct e.actor_id as 'internal_id' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
            and e.action ='closed' and e.created_at > '%s' and e.created_at <= '%s';"""
            % (project_id, project_id, start, end), con=db)
        d_closed_internal_time = pd.read_sql("""select i.id, i.issue_id, i.created_at as 'open_time',
            e.created_at as 'close_time' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.reporter_id in
            (select distinct e.actor_id as 'internal_id' from `ghtorrent-2018-03`.issues i,
            `ghtorrent-2018-03`.issue_events e where i.repo_id = '%i' and
            e.action = 'closed' and i.id = e.issue_id and e.actor_id <> i.reporter_id)
            and i.repo_id = '%i' and i.pull_request_id is NULL and i.id = e.issue_id
            and e.action ='closed' and e.created_at > '%s' and e.created_at <= '%s';"""
            % (project_id, project_id, start, end), con=db)
        d_closed_pr_time = pd.read_sql("""select i.id, i.pull_request_id as 'issue_id', i.created_at as 'open_time',
            p.created_at as 'close_time' from `ghtorrent-2018-03`.pull_request_history p,
            `ghtorrent-2018-03`.issues i where i.repo_id = '%i' and i.pull_request_id
            is not NULL and i.pull_request_id = p.pull_request_id and p.action ='closed'
            and p.created_at > '%s' and p.created_at <= '%s';"""
            % (project_id, start, end), con=db)

    df_data_temp = pd.DataFrame(columns=['project_id', 'slug', 'month_index', 'num_commit',
        'num_closed', 'num_closed_external', 'num_closed_internal', 'num_closed_pr',
        'id', 'issue_id', 'open_time', 'close_time', 'age', 'close_type'])
    # if nums are all 0, then don't need to deal with time
    num_closed = d_closed['num_closed'].values[0]
    num_closed_external = d_closed_external['num_closed_external'].values[0]
    num_closed_internal = d_closed_internal['num_closed_internal'].values[0]
    num_closed_pr = d_closed_pr['num_closed_pr'].values[0]
    num_commit = d_commit['num_commit'].values[0]
    if num_closed == 0 and num_closed_external == 0 and num_closed_internal == 0 and num_closed_pr == 0:
        df_data_temp = df_data_temp.append({'project_id':project_id, 'slug':slug, 'month_index':index-9,
            'num_commit':num_commit, 'num_closed':0, 'num_closed_external':0, 'num_closed_internal':0,
            'id':np.nan, 'issue_id':np.nan,
            'num_closed_pr':0,'open_time':np.nan, 'close_time':np.nan, 'age':np.nan,
            'close_type':np.nan}, ignore_index=True)
    else:
        d_closed_time['close_type'] = 'closed'
        d_closed_external_time['close_type'] = 'closed_external'
        d_closed_internal_time['close_type'] = 'closed_internal'
        d_closed_pr_time['close_type'] = 'closed_pr'
        df_time = pd.concat([d_closed_time, d_closed_external_time,
            d_closed_internal_time, d_closed_pr_time])
        df_time['age'] = df_time['close_time'].apply(convert_datetime) - df_time['open_time'].apply(convert_datetime)
        df_time['age'] = df_time['age'].apply(clean_timedelta)
        df_data_temp.open_time = df_time.open_time
        df_data_temp.close_time = df_time.close_time
        df_data_temp.close_type = df_time.close_type
        df_data_temp.id = df_time.id
        df_data_temp.issue_id = df_time.issue_id
        df_data_temp.age = df_time.age
        df_data_temp.project_id = project_id
        df_data_temp.slug = slug
        df_data_temp.month_index = index-9
        df_data_temp.num_commit = num_commit
        df_data_temp.num_closed = num_closed
        df_data_temp.num_closed_external = num_closed_external
        df_data_temp.num_closed_internal = num_closed_internal
        df_data_temp.num_closed_pr = num_closed_pr
    return df_data_temp

# Get other project ids
def get_project_ids(project_id, slug, db):
    df_name = pd.read_sql("""select p.name, p.created_at from `ghtorrent-2018-03`.projects p where
        p.id = '%i';""" % (project_id), con=db)
    name = df_name['name'].values[0]
    created_at = df_name['created_at'].values[0]
    df_projects = pd.read_sql("""select p.url, p.id as 'project_id' from `ghtorrent-2018-03`.projects p
        where p.name='%s' and p.forked_from is NULL and p.created_at='%s';"""
        % (name, created_at), con=db)
    project_ids = [(project_id, slug)]
    for index, row in df_projects.iterrows():
        id = row['project_id']
        slug = '/'.join(row['url'].split('/')[-2:])
        if id not in dict(project_ids):
            project_ids.append((id, slug))
    return project_ids

# Get adoption metrics
def get_data(boundaries, df_data, project_id, slug):
    projects = get_project_ids(project_id, slug, db)
    # Break up boundaries into a list of pairs
    boundaries2 = [boundaries[i:i+2] for i in range(0, len(boundaries), 1)][:-1]
    # Create a connection object
    db = mysql.connector.connect(host='localhost', user='', passwd='', database='ghtorrent-2018-03')
    # Create a cursor object to interact with the server
    cur = db.cursor()
    # Iterate through boundaries2 and run sql commands
    for index, interval in enumerate(boundaries2):
        start = str(interval[0])
        end = str(interval[1])
        for project in projects:
            (project_id, slug) = project
            df_data_temp = get_month_data(start, end, project_id, index, slug, db)
            num_closed = df_data_temp['num_closed'].values[0]
            num_closed_external = df_data_temp['num_closed_external'].values[0]
            num_closed_internal = df_data_temp['num_closed_internal'].values[0]
            num_closed_pr = df_data_temp['num_closed_pr'].values[0]
            num_commit = df_data_temp['num_commit'].values[0]
            if num_commit == 0 and num_closed == 0 and num_closed_external == 0 and num_closed_internal == 0 and num_closed_pr == 0:
                continue
            else:
                df_data = df_data.append(df_data_temp, ignore_index=True)
                break
    return df_data

def query(row):
    df_data = pd.DataFrame(columns=['project_id', 'slug', 'month_index', 'num_commit',
        'num_closed', 'num_closed_external', 'num_closed_internal', 'num_closed_pr',
        'id', 'issue_id', 'open_time', 'close_time', 'age', 'close_type'])

    slug = row['slug']
    project_id = df_metric[df_metric.slug==slug].project_id.values[0]
    earliest_date = row['date']
    boundaries = get_boundaries(earliest_date)

    # introduced the service nine months before May 23 2019 (last element in
    # boundaries should be earlier than May 23 2019), created at least
    # nine months before introduction (first element in boundaries should be
    # later than created_at date)
    may = convert_datetime('2019-05-23')
    created_at = convert_datetime(df_metric[df_metric.slug==slug].created_at.values[0])
    if boundaries[-1] <= may and boundaries[0] >= created_at:
        result = get_data(boundaries, df_data, project_id, slug)
        return (result, None)
    else:
        # print(slug)
        return (None, slug)

if __name__ == "__main__":
    start = time.time()
    # Open CSV files with funding ask dates
    df_npm = pd.read_csv('files/20190728_npm_asking_adoption_money.csv')
    df_gh = pd.read_csv('files/20190722_github_asking_adoption_money.csv')
    df = pd.concat([df_npm, df_gh], ignore_index=True).drop_duplicates()
    df_suitable = df[df.suitable == 1]
    dicts = df_suitable.to_dict('records')
    df_adoption = pd.DataFrame(columns=['project_id', 'slug', 'month_index', 'num_commit',
        'num_closed', 'num_closed_external', 'num_closed_internal', 'num_closed_pr',
        'id', 'issue_id', 'open_time', 'close_time', 'age', 'close_type'])
    excluded = []
    pool = Pool(processes=8)
    for result in pool.imap_unordered(query, tqdm(dicts[:])):
        (df, error) = result
        if df is not None:
            df_adoption = df_adoption.append(df, ignore_index=True)
        else:
            excluded.append(error)

    # make dataframes
    df_adoption.to_csv('insert file name', index=False)
    pd.Series(excluded, name='slug').to_csv('insert file name', header=True, index=False)
    end = time.time()
    print(end-start) # Gives time in seconds
