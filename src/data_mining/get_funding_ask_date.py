# Generate a CSV with information on when a funding service
# is added or removed from a project. Repos need to be downloaded locally.
from collections import defaultdict
import os
from git import Repo
import csv
import pandas as pd
import time
import datetime
from multiprocessing import Pool
from tqdm import tqdm

services_dict = {
            'salt.bountysource.com/':'salt',
            'tidelift.com/subscription/':'tidelift',
            'otechie.com/':'otechie',
            'bountysource.com/':'bountysource',
            'flattr.com/':'flattr',
            'issuehunt.io/':'issuehunt',
            'kickstarter.com/':'kickstarter',
            'liberapay.com/':'liberapay',
            'gratipay.com/':'liberapay',
            'opencollective.com/':'opencollective',
            'patreon.com/':'patreon',
            'paypal.com/':'paypal',
            'paypal.me/':'paypal',
            'tip4commit.com/':'tip4commit'
            }
# list paths containing downloaded repos
ref_paths = ['']
# Make funding service DataFrame
services_df = pd.DataFrame(services_dict.items(), columns=['keyword', 'service'])
# Group keywords by same service
services_df = services_df.groupby(['service'])['keyword'].apply(','.join).reset_index()
# Add added column
services_df['added'] = False
search_terms = ['readme.md']
EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

def getfilenames(repo):
    head_tree = repo.head.commit.tree
    filenames = []
    for blob in head_tree.blobs:
        if blob.path.lower() in search_terms:
            filenames.append(blob.path)
    return filenames

def search(data):
    results = []
    (repo_path, slug) = data
    try:
        # Use GitPython to get dates that any service is added/removed
        repo = Repo(repo_path)
    except:
        results.append(([slug, 'unknown', 'unknown', datetime.time().strftime("%Y-%m-%d %H:%M"), 'unknown', 'loaderror'],True))
        return results
    # Check that the repository loaded correctly
    if not repo.bare:
        try:
            git = repo.git
            # Get current active_branch
            branch = repo.active_branch
            # Get filename(s)
            filenames = getfilenames(repo)
            # if filenames  empty, get to except
            if not filenames:
                raise ValueError('no readme found')
            # else iterate through filenames
            for filename in filenames:
                # Get commits associated with filename
                commits = repo.iter_commits(branch.name, paths=filename)
                # Reset added column
                services_df['added'] = False
                # For each commit, get the tree and read in the relevant file
                for commit in reversed(list(commits)):
                    sha = str(commit.hexsha)
                    date = commit.committed_datetime.strftime("%Y-%m-%d %H:%M")
                    # Get the text of the filename from the commit sha
                    try:
                        text = git.show('{}:{}'.format(sha, filename))
                    except:
                        results.append(([slug, filename, sha, date, 'unknown', 'corrupt'], True))
                        break
                    # Check for added case
                    keywords = services_df['keyword'].values
                    for keyword in keywords:
                        added = services_df.loc[services_df.keyword==keyword, 'added'].values[0]
                        service = services_df.loc[services_df.keyword==keyword, 'service'].values[0]
                        # Check if keyword contains multiple
                        if ',' in keyword:
                            words = keyword.split(',')
                        else:
                            words = [keyword]
                        if any(word in str(text) for word in words) and not added:
                            services_df.loc[services_df.keyword==keyword, 'added'] = True
                            results.append(([slug, filename, sha, date, service, 'add'], False))
                        # Check for removed case
                        elif all(word not in str(text) for word in words) and added:
                            services_df.loc[services_df.keyword==keyword, 'added'] = False
                            results.append(([slug, filename, sha, date, service, 'remove'], False))
        except ValueError as err:
            # No readme found
            results.append(([slug, 'unknown', 'unknown', datetime.time().strftime("%Y-%m-%d %H:%M"), 'unknown', 'noreadme'], True))
            return results
        except:
            # Error happened, increment num_errors
            results.append(([slug, 'unknown', 'unknown', datetime.time().strftime("%Y-%m-%d %H:%M"), 'unknown', 'giterror'], True))
            return results
    else:
        results.append(([slug, 'unknown', 'unknown', datetime.time().strftime("%Y-%m-%d %H:%M"), 'unknown', 'loaderror'], True))
        return results
    return results

def get_repo_path(slug):
    repo_name = slug.replace('/', '_____')
    paths = []
    # Check to see which ref_path to use
    for ref_path in ref_paths:
        if os.path.exists(ref_path+repo_name):
            path = ref_path+repo_name
            paths.append(path)
    if len(paths) > 1:
        print(slug)
    elif not paths:
        return None
    return paths[0]

def get_dates(slug):
    repo_path = get_repo_path(slug)
    if repo_path is None:
        return (None, slug)
    return (search((repo_path, slug)), None)

if __name__ == "__main__":
    # Open csv containing list of slugs
    df = pd.read_csv('insert file name', usecols=[0])
    slugs = df['slug'].values
    missing_path = []
    csv_data = []
    csv_name = 'insert file name'
    append_counter = 0
    num_errors = 0
    pool = Pool(processes=8)
    for results in pool.imap_unordered(get_dates, tqdm(slugs[:])):
        if results[0] is None:
            missing_path.append(results[1])
        else:
            for result in results[0]:
                (data, error) = result
                csv_data.append(data)
                if error:
                    num_errors += 1
                append_counter += 1
                # every 10000 directories, append to csv
                if append_counter % 10000 == 0:
                    if append_counter == 10000:
                        # first time write
                        with open(csv_name, 'w') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerows(csv_data)
                        csv_file.close()
                    else:
                        with open(csv_name, 'a') as csv_file:
                            writer = csv.writer(csv_file)
                            writer.writerows(csv_data)
                        csv_file.close()
                    csv_data = []
    if csv_data:
        if append_counter <= 10000:
            # first time write
            with open(csv_name, 'w') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(csv_data)
            csv_file.close()
        else:
            with open(csv_name, 'a') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerows(csv_data)
            csv_file.close()
    print('Number of errors:', num_errors)
