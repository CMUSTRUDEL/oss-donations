# Get top download npm control group
import pandas as pd
import numpy as np
from tqdm import tqdm
import time
import mysql.connector
from multiprocessing import Pool

# Open funding_slugs.csv and get slug names
slugs = pd.read_csv('files/20190614_funding_slugs.csv', header=None)
slugs.columns = ['slug']
slugs_lst = slugs['slug'].values

urls = ['https://api.github.com/repos/', 'https://api./repos/']

def get_download(id, db):
    try:
        df_data = pd.read_sql("""select sum(d.downloads) as 'num_download'
            from badges.funding_downloads d,
            `ghtorrent-2018-03`.projects p where d.name = p.name and p.id = '%i';"""
                % id, con=db)
        if df_data.empty:
            raise
        # Get the sum of the downloads column
        return (df_data['num_download'].values[0], None)
    except:
        return (None, id)

def get_info(slug):
    # Create a connection object
    db = mysql.connector.connect(host='localhost', user='', passwd='', database='ghtorrent-2018-03')
    # Create a cursor object to interact with the server
    cur = db.cursor()

    # Make sure the slug isn't in slugs_lst
    if slug in slugs_lst:
        return (None, None)

    slug_urls = [url+slug for url in urls]
    try:
        # read_sql() reads a SQL query into a df
        df_slug = pd.read_sql("""select p.id as 'project_id' from projects p
            where p.url = '%s';""" % slug_urls[0],
                con=db)
        if df_slug.empty:
            raise

    except:
        try:
            df_slug = pd.read_sql("""select p.id as 'project_id' from projects p
                where p.url = '%s';""" % slug_urls[1],
                    con=db)
            if df_slug.empty:
                # Nothing for that project found
                return (None, slug)
        except:
            return (None, slug)

    if df_slug.shape[0] > 1:
        return (None, slug)
    else:
        (num_download, error) = get_download(df_slug.project_id.values[0], db)
        if num_download is not None:
            df_slug['num_download'] = num_download
        else:
            return (None, slug)

    df_slug['slug'] = slug

    return (df_slug, None)

if __name__ == "__main__":
    start = time.time()
    errors = []
    # Open list of npm slugs
    lines = [line.rstrip('\n') for line in open('files/20190702_npm_slugs.txt', encoding='utf8', errors='ignore')]

    # Make dataframe
    df_download = pd.DataFrame(columns = ['project_id', 'slug', 'num_download'])

    pool = Pool(processes=8)

    for result in pool.imap_unordered(get_info, tqdm(lines[:])):
        (df, error) = result
        if df is not None:
            df_download = df_download.append(df, ignore_index=True, sort=False)
        elif error is not None:
            errors.append(error)

    df_download = df_download.sort_values(by='num_download', ascending=False)

    # save df_owner_username
    # df_download.head(20000).to_csv('insert file name', index=False)
    end = time.time()
    print(end-start) # Gives time in seconds
