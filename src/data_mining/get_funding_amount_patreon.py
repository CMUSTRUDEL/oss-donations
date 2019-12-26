# This script gets the amount of funding gained within 9 months
# of the first date
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
# Need to merge two patreon stat CSV files
df_patreon1 = pd.read_csv('files/20190714_github_patreon_stats.csv')
df_patreon2 = pd.read_csv('files/20190627_patreon_stats.csv')
df_patreon = pd.concat([df_patreon1, df_patreon2], ignore_index=True).drop_duplicates()

df_data = pd.read_csv('files/20190727_asking_all.csv')

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

def get_patreon_money(start, end, url):
    df_url = df_patreon[df_patreon.patreon_url==url]
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

def get_money(start, end, slug):
    patreon_url = df_data[df_data.slug==slug].patreon_url.values[0]
    if not pd.isna(patreon_url):
        earning = get_patreon_money(start, end, patreon_url)
        return earning
    else:
        print(slug)
        return None

def query(row):
    slug = row['slug']
    first_date = convert_datetime(row['first_date'])
    earning = None
    if not pd.isna(first_date):
        first_date_boundary = get_boundaries(first_date)
        earning = get_money(first_date, first_date_boundary[-1], slug)
    return earning

if __name__ == "__main__":
    df = pd.read_csv('files/20190730_patreon_adoption_dates.csv')
    dicts = df.to_dict('records')
    df_money = pd.DataFrame(columns=['slug', 'earning_after_first_date'])
    for row in tqdm(dicts[:]):
        first_date_earning = query(row)
        df_money = df_money.append({'slug':row['slug'], 'earning_after_first_date':first_date_earning}, ignore_index=True)
    df_money.to_csv('insert file name', index=False)
