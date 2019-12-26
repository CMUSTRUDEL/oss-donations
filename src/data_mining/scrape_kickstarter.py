# Script used to scrape funding info from kickstarter pages
import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re
from datetime import datetime
import ast
import dateutil.relativedelta
from tqdm import tqdm

urls = set()
num_duplicates = 0

def convert_datetime(x):
    try:
        temp = datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            temp = datetime.strptime(x, '%m/%d/%Y %H:%M')
        except:
            try:
                temp = datetime.strptime(x, '%m/%d/%Y %H:%M:%S')
            except:
                try:
                    temp = datetime.strptime(x, '%b %d, %Y')
                except:
                    temp = datetime.strptime(x, '%Y-%m-%d')
    return temp

def get_stats(url):
    df = pd.DataFrame(columns=['url', 'earning_last9months', 'total_earning',
        'num_backer', 'goal', 'start_date', 'end_date'])

    try:
        source = requests.get(url).text
    except:
        df = df.append({'url':url, 'earning_last9months':np.nan, 'total_earning':np.nan,
            'num_backer':np.nan, 'goal':np.nan, 'start_date':np.nan, 'end_date':np.nan},
            ignore_index=True)
        return df

    soup = BeautifulSoup(source, 'html.parser')
    # Get amount
    h3s = soup.find_all("h3", class_="mb0")
    amount = np.nan
    for h3 in h3s:
        moneys = h3.find_all("span", class_="money")
        if len(moneys) >= 1:
            amount_str = moneys[0].string
            amount_str = ''.join(c for c in amount_str if c.isdigit())
            amount = float(amount_str)
            break
    # Get number of backers
    divs = soup.find_all("div", class_="mb0")
    num_backers = np.nan
    for div in divs:
        if 'backer' in str(div):
            num_backers_str = div.find_all("h3", class_="mb0")[0].string
            num_backers_str = ''.join(c for c in num_backers_str if c.isdigit())
            num_backers = int(num_backers_str)
            break
    # Get goal
    divs = soup.find_all("div", class_="mb3")
    goal_amount = np.nan
    for div in divs:
        goals = div.find_all("div", class_="type-12 medium navy-500")
        if len(goals) >= 1:
            for goal in goals:
                if 'goal' in str(goal):
                    # Get the money
                    moneys = goal.find_all("span", class_="money")
                    if len(moneys) >= 1:
                        goal_amount_str = moneys[0].string
                        goal_amount_str = ''.join(c for c in goal_amount_str if c.isdigit())
                        goal_amount = float(goal_amount_str)
                        break
            else:
                continue
            break
    # Get compaign start and end dates
    divs = soup.find_all("div", class_="NS_campaigns__funding_period")
    start = np.nan
    end = np.nan
    for div in divs:
        if 'Funding period' in str(div):
            ps = div.find_all("p", class_="f5")
            if ps:
                times = ps[0].find_all("time")
                if len(times) != 2:
                    break
                start = convert_datetime(times[0].string)
                end = convert_datetime(times[1].string)
                break
    # Check if end date is within 9 months
    if end is not np.nan and end <= convert_datetime('2019-05-23') and end >= convert_datetime('2018-08-23'):
        earning_last9months = amount
    elif end is not np.nan and start is not np.nan and amount is not np.nan:
        earning_last9months = 0
    elif end is not np.nan and start is not np.nan and amount is np.nan: # funding unsuccessful
        amount = 0
        earning_last9months = 0
    else:
        earning_last9months = np.nan
    df = df.append({'url':url, 'earning_last9months':earning_last9months, 'total_earning':amount,
        'num_backer':num_backers, 'goal':goal_amount, 'start_date':start, 'end_date':end},
        ignore_index=True)
    return df

if __name__ == "__main__":
    # Open csv with kickstarter urls
    df_data = pd.read_csv('files/20190711_github_kickstarter_url.csv')
    df_output = pd.DataFrame(columns=['slug', 'service', 'filename', 'url',
        'earning_last9months', 'total_earning', 'num_backer', 'goal',
        'start_date', 'end_date'])
    grouped = df_data.groupby('url', sort=False)
    for url, df_url in tqdm(grouped):
        df_money = get_stats(url)
        df_merge = df_url.merge(df_money, on='url')
        df_output = df_output.append(df_merge, ignore_index=True, sort=False)

    # df_output.to_csv('insert file name', index=False)
