# This script gets the following opencollective info
# earning_after_first_date
# expense_after_first_date
# earning_after_first_expense
# expense_after_first_expense
# The time range for all of these metrics is in the 9 months after
# the first date or first expense

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm

df_data = pd.read_csv('files/20190727_asking_all.csv')

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
    intro_right = intro_time + timedelta(days=15)
    # compute boundaries of panel intervals
    num_window = 9
    delta = 30
    boundaries = [intro_right]
    boundaries += [intro_right + i * timedelta(days=delta) for i in range(1, num_window+1, 1)]
    return boundaries

def get_oc_money(start, end, url):
    start = start.strftime('%Y-%m-%d')
    end = end.strftime('%Y-%m-%d')
    path = 'files/20190719_OpenCollective CSV'
    directory = os.fsencode(path)
    earning = 0
    expense = 0
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
            expense = df_oc[(df_oc['Transaction Amount'] < 0)&
                (df_oc['Transaction Date'] >= start)&
                (df_oc['Transaction Date'] <= end)]['Transaction Amount'].sum()
            return (earning, expense)
    return (earning, expense)

# Get money earned in 9 months after adoption
def get_money(start, end, slug):
    oc_url = df_data[df_data.slug==slug].opencollective_url.values[0]
    if not pd.isna(oc_url):
        (earning, expense) = get_oc_money(start, end, oc_url)
        return (earning, expense)
    else:
        print(slug)
        return (None, None)

def query(row):
    # Get the first introduction date
    slug = row['slug']
    first_date = convert_datetime(row['first_date'])
    first_expense = convert_datetime(row['first_expense_date'])
    first_date_earning = None
    first_expense_earning = None
    first_date_expense = None
    first_expense_expense = None
    if not pd.isna(first_date):
        first_date_boundary = get_boundaries(first_date)
        (first_date_earning, first_date_expense) = get_money(first_date, first_date_boundary[-1], slug)
    if not pd.isna(first_expense):
        first_expense_boundary = get_boundaries(first_expense)
        (first_expense_earning, first_expense_expense) = get_money(first_expense, first_expense_boundary[-1], slug)
    return (first_date_earning, first_date_expense, first_expense_earning, first_expense_expense)

if __name__ == "__main__":
    # Open adoption_slugs.csv
    df = pd.read_csv('files/20190727_oc_adoption_dates.csv')
    dicts = df.to_dict('records')
    df_money = pd.DataFrame(columns=['slug', 'earning_after_first_date', 'expense_after_first_date',
    'earning_after_first_expense', 'expense_after_first_expense'])
    for row in tqdm(dicts[:]):
        (first_date_earning, first_date_expense, first_expense_earning, first_expense_expense) = query(row)
        df_money = df_money.append({'slug':row['slug'], 'earning_after_first_date':first_date_earning,
            'expense_after_first_date':first_date_expense,'earning_after_first_expense':first_expense_earning,
            'expense_after_first_expense':first_expense_expense}, ignore_index=True)

    df_money.to_csv('insert file name', index=False)
