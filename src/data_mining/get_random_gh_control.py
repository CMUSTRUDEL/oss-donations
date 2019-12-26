import pandas as pd
import numpy as np
import mysql.connector
import random

urls = ['https://api.github.com/repos/', 'https://api./repos/']
num_projects = 137611262
df_asking = pd.read_csv('files/20190727_asking_all.csv', usecols=[1])
slugs = df_asking.slug.values

def get_slug(url):
    slug = '/'.join(url.split('/')[-2:])
    return slug

def get_random_project(db):
    # Generate random number
    project_id = random.randint(1,num_projects+1)
    # Get url from database
    df_slug = pd.read_sql("""select p.url, p.forked_from from `ghtorrent-2018-03`.projects p
        where p.id = '%i';""" % project_id, con=db)
    if df_slug.empty:
        return None
    elif df_slug.shape[0] > 1:
        return None
    dict = df_slug.to_dict('records')[0]
    if not pd.isna(dict['forked_from']):
        return None
    slug = get_slug(dict['url'])
    if slug in slugs:
        return None
    return (project_id, slug, dict['forked_from'])

if __name__ == "__main__":
    # Create a connection object
    db = mysql.connector.connect(host='localhost', user='', passwd='', database='ghtorrent-2018-03')
    # Create a cursor object to interact with the server
    cur = db.cursor()
    df_sample = pd.DataFrame(columns=['project_id', 'slug', 'forked_from'])
    count = 0
    while count < 200000:
        result = get_random_project(db)
        if result is not None:
            (project_id, slug, forked_from) = result
            if slug not in df_sample.slug.values:
                print(slug)
                df_sample = df_sample.append({'project_id':project_id, 'slug':slug, 'forked_from':forked_from}, ignore_index=True)
                count += 1

    df_sample.to_csv('insert file name', index=False)
