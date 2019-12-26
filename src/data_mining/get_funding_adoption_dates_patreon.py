# This script gets the first date associated with a list of
# patreon urls
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm
# Need to merge two patreon stat CSV files
df_patreon1 = pd.read_csv('files/20190714_github_patreon_stats.csv')
df_patreon2 = pd.read_csv('files/20190627_patreon_stats.csv')
df_patreon = pd.concat([df_patreon1, df_patreon2], ignore_index=True).drop_duplicates()

def convert_datetime(x):
    if not isinstance(x, str):
        return x
    # Ignore time zone info
    if 'T' in x and 'Z' in x:
        x = x.split('T')[0]
    try:
        temp = datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            temp = datetime.strptime(x, '%Y-%m-%d')
        except:
            try:
                temp = datetime.strptime(x, '%m/%d/%Y')
            except:
                try:
                    temp = datetime.strptime(x, '%m/%d/%Y %H:%M:%S')
                except:
                    temp = datetime.strptime(x, '%m/%d/%Y %H:%M')
    return temp

def get_date(url):
    df_patreon_temp = df_patreon[df_patreon.patreon_url==url]
    months = df_patreon_temp['month'].dropna()
    if not months.empty:
        return months.values[-1]
    return None

if __name__ == "__main__":
    df_data = pd.read_csv('files/20190727_asking_all.csv')
    df_sub = df_data[df_data.patreon==1].copy()
    df_sub['first_date'] = np.nan
    # Get list of urls with patreon
    urls = list(set(df_sub.patreon_url.dropna().values))
    # Go through urls
    for url in tqdm(urls):
        date = get_date(url)
        if date is not None:
            for index, row in df_sub[df_sub.patreon_url==url].iterrows():
                df_sub.loc[index, 'first_date'] = date

    df_sub.to_csv('insert file name', index=False, columns=['slug', 'first_date'])
