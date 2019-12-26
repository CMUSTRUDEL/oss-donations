# This script gets monthly earning data for opencollective and patreon projects
# used for RDD.
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm

# Open CSV file of relevant projects with their corresponding funding data
df_all = pd.read_csv('files/20190727_asking_all.csv')
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

def get_oc_money(start, end, url):
    try:
        start = start.strftime('%Y-%m-%d')
        end = end.strftime('%Y-%m-%d')
        path = 'files/20190719_OpenCollective CSV'
        directory = os.fsencode(path)
        earning = 0
        url_name = url.split('#')[0].rstrip()
        url_name = url_name.split('/')[-1]
        url_name = url_name.split(' ')[0]
        for file in os.listdir(directory):
            file = file.decode("utf-8")
            name = file.split('--')[0]
            if name == url_name.lower():
                df_oc = pd.read_csv(path+'/'+file)
                # Get data from df_oc
                df_oc['Transaction Date'] = df_oc['Transaction Date'].apply(convert_datetime)
                earning = df_oc[(df_oc['Transaction Amount'] > 0)&
                    (df_oc['Transaction Date'] >= start)&
                    (df_oc['Transaction Date'] <= end)]['Transaction Amount'].sum()
                return earning
        return earning
    except:
        print('errored')
        return 0

def get_patreon_money(start, end, df_url):
    try:
        start = start.strftime('%Y-%m-%d')
        end = end.strftime('%Y-%m-%d')
        amounts = df_url['amount'].dropna()
        patrons = df_url['patrons'].dropna()
        month_earnings = df_url['month_earning'].dropna()
        months = df_url['month'].dropna()
        if not months.empty:
            df_temp = pd.DataFrame({'month':months, 'month_earning':month_earnings}, columns=['month', 'month_earning'])
            df_temp.month = df_temp.month.apply(convert_datetime)
            earning = df_temp[(df_temp.month >= start)&
                (df_temp.month <= end)].month_earning.sum()
        elif not amounts.empty:
            amount = amounts.values[0]
            earning = 9*(amount)
        elif not patrons.empty:
            patron = patrons.values[0]
            if patron == 0:
                earning = 0
            else:
                earning = np.nan
        else:
            earning = 0
        return earning
    except:
        print('errored')
        return 0

def get_money(row, interval):
    start = interval[0]
    end = interval[1]
    money = 0
    if row['patreon'] == 1:
        patreon_url = df_all[df_all.slug==row['slug']].patreon_url.values[0]
        if not pd.isna(patreon_url):
            df_patreon_temp = df_patreon[df_patreon.patreon_url==patreon_url]
            patreon_money = get_patreon_money(datetime(start.year, start.month, 1),
                datetime(end.year, end.month, 1), df_patreon_temp)
            money += patreon_money
    if row['opencollective'] == 1:
        oc_url = df_all[df_all.slug==row['slug']].opencollective_url.values[0]
        if not pd.isna(oc_url):
            oc_money = get_oc_money(start, end, oc_url)
            money += oc_money
    return money

def query(row):
    slug = row['slug']
    date = row['date']
    df = pd.DataFrame(columns=['slug', 'month_index', 'earning'])
    boundaries = get_boundaries(date)
    boundaries2 = [boundaries[i:i+2] for i in range(0, len(boundaries), 1)][:-1]
    for index, interval in enumerate(boundaries2):
        earning = get_money(row, interval)
        df = df.append({'slug':slug, 'month_index':index-9, 'earning':earning},
            ignore_index=True)
    return df

if __name__ == "__main__":
    # Open CSV file with date of asking or getting funding
    df = pd.read_csv('files/20190821_get_dates.csv')
    dicts = df.to_dict('records')
    df_money = pd.DataFrame(columns=['slug', 'month_index', 'earning'])
    for row in tqdm(dicts[:]):
        result = query(row)
        if not result.empty:
            df_money = df_money.append(result, ignore_index=True)
    df_money.to_csv('insert file name', index=False)
