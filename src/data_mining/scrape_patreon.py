# This script scraps patreon and graphtreon. It outputs
# 20190714_github_patreon_stats.csv and 20190627_patreon_stats.csv,
# which are used in other scripts
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
errors = []
append_counter = 0

def convert_datetime(date):
    return datetime.strptime(date, '%b%d%Y')

def get_stats(url):
    # Generate graphtreon url
    graphtreon_url = 'https://graphtreon.com/creator/' + url.split('/')[-1]
    try:
        source = requests.get(url).text
    except:
        errors.append(url)
        return None

    soup = BeautifulSoup(source, 'html.parser')
    # Get number of patrons and $ obtained per month
    try:
        h2s = soup.find_all("h2", class_="sc-bZQynM izRyKA")
        if len(h2s) > 1:
            num_patron_str = h2s[0].string.replace(',', '')
            if 'k' in num_patron_str:
                num_patron = int(num_patron_str.replace('k', ''))
                num_patron = num_patron * 1000
            else:
                num_patron = int(num_patron_str)
            amount_str = h2s[1].string[1:].replace(',', '')
            if 'k' in amount_str:
                amount = float(amount_str.replace('k', ''))
                amount = amount * 1000
            else:
                amount = float(amount_str)
        elif len(h2s) > 0:
            num_patron_str = h2s[0].string.replace(',', '')
            if '$' in num_patron_str:
                amount_str = num_patron_str[1:]
                if 'k' in amount_str:
                    amount = float(amount_str.replace('k', ''))
                    amount = amount * 1000
                else:
                    amount = float(amount_str)
                num_patron = np.nan
            else:
                if 'k' in num_patron_str:
                    num_patron = int(num_patron_str.replace('k', ''))
                    num_patron = num_patron * 1000
                else:
                    num_patron = int(num_patron_str)
                amount = np.nan
        else:
            num_patron = np.nan
            amount = np.nan
    except:
        print(url)
    # Get goal
    try:
        span = soup.find_all("span", class_="sc-htpNat ebhhXb")[0].string
        if '$' in span:
            goal_str = span.split('$')[-1].replace(',', '')
            if 'k' in goal_str:
                goal = float(goal_str.replace('k', ''))
                goal = goal * 1000
            else:
                goal = float(goal_str)
            percent_goal = np.nan
        elif '%' in span:
            percent_goal = float(span.split('%')[0])
            goal = np.nan
        else:
            percent_goal = np.nan
            goal = np.nan
    except:
        percent_goal = np.nan
        goal = np.nan

    df_stats = pd.DataFrame(columns=['patreon_url', 'graphtreon_url',
        'patrons', 'amount', 'goal', 'percent_goal', 'creator_name', 'launch_date',
        'day', 'day_patron', 'day_earning','month', 'month_patron', 'month_earning'])

    if amount == 0 and num_patron == 0:
        df_stats = df_stats.append({'patreon_url':url, 'graphtreon_url':graphtreon_url,
            'patrons':num_patron, 'amount':amount, 'goal':goal, 'percent_goal':percent_goal,
            'creator_name':np.nan, 'launch_date':np.nan,
            'day':np.nan, 'day_patron':np.nan, 'day_earning':np.nan,
            'month':np.nan, 'month_patron':np.nan, 'month_earning':np.nan}, ignore_index=True)
        return df_stats
    # Get graphtreon data
    try:
        source = requests.get(graphtreon_url).text
    except:
        df_stats = df_stats.append({'patreon_url':url, 'graphtreon_url':graphtreon_url,
            'patrons':num_patron, 'amount':amount, 'goal':goal, 'percent_goal':percent_goal,
            'creator_name':np.nan, 'launch_date':np.nan,
            'day':np.nan, 'day_patron':np.nan, 'day_earning':np.nan,
            'month':np.nan, 'month_patron':np.nan, 'month_earning':np.nan}, ignore_index=True)
        return df_stats

    soup = BeautifulSoup(source, 'html.parser')
    # Get the launched date
    header_spans = soup.find_all("span", class_="headerstats-header")
    content_spans = soup.find_all("span", class_="headerstats-stat")
    launch_date = ''

    for index, span in enumerate(header_spans):
        try:
            span_str = re.sub(r'\W+', '', span.string)
            # print(span_str)
            if span_str == 'Launched':
                launch_date = re.sub(r'\W+', '', content_spans[index].string)
        except:
            continue

    if not launch_date:
        df_stats = df_stats.append({'patreon_url':url, 'graphtreon_url':graphtreon_url,
            'patrons':num_patron, 'amount':amount, 'goal':goal, 'percent_goal':percent_goal,
            'creator_name':np.nan, 'launch_date':np.nan,
            'day':np.nan, 'day_patron':np.nan, 'day_earning':np.nan,
            'month':np.nan, 'month_patron':np.nan, 'month_earning':np.nan}, ignore_index=True)
        return df_stats

    launch_date = convert_datetime(launch_date)

    # Get the variables within the script
    variables = ['var creatorName = ', 'var dailyGraph_patronSeriesData = ',
        'var dailyGraph_earningsSeriesData = ', 'var monthlyGraph_patronSeriesData = ', 'var monthlyGraph_earningsSeriesData = ']

    results = []
    scripts = soup.find_all('script')

    # Get end dates
    daily_end = convert_datetime('Jun252019')
    monthly_end = convert_datetime('May012019')
    try:
        for script in scripts:
            if 'var creatorName =' in script.text:
                text = script.text
                for var in variables[:]:
                    index = text.find(var)
                    if index != -1:
                        end_index = text.find(';', index)
                        start_index = index+len(var)
                        res = text[start_index:end_index]
                        res = res.replace('\'', '')
                        if '[' in res:
                            res = ast.literal_eval(res)
                        results.append(res)
    except:
        df_stats = df_stats.append({'patreon_url':url, 'graphtreon_url':graphtreon_url,
            'patrons':num_patron, 'amount':amount, 'goal':goal, 'percent_goal':percent_goal,
            'creator_name':np.nan, 'launch_date':launch_date,
            'day':np.nan, 'day_patron':np.nan, 'day_earning':np.nan,
            'month':np.nan, 'month_patron':np.nan, 'month_earning':np.nan}, ignore_index=True)
        return df_stats

    if len(results) == 5:
        # Separate monthly data
        month_temp = monthly_end
        monthly_patron = list(reversed(results[3]))
        monthly_earning = list(reversed(results[4]))
        monthly_patron_dict = dict(monthly_patron)
        monthly_earning_dict = dict(monthly_earning)
        combo = [(monthly_patron_dict[id], monthly_earning_dict[id]) for id in set(monthly_patron_dict) & set(monthly_earning_dict)]
        for pair in combo:
            df_stats = df_stats.append({'day':np.nan, 'day_patron':np.nan, 'day_earning':np.nan,
                'month':month_temp, 'month_patron':pair[0], 'month_earning':pair[1]}, ignore_index=True)
            month_temp = month_temp - dateutil.relativedelta.relativedelta(months=1)

        # Separate daily data
        day_temp = daily_end
        daily_patron = list(reversed(results[1]))
        daily_earning = list(reversed(results[2]))
        daily_patron_dict = dict(daily_patron)
        daily_earning_dict = dict(daily_earning)
        combo = [(daily_patron_dict[id], daily_earning_dict[id]) for id in set(daily_patron_dict) & set(daily_earning_dict)]
        for pair in combo:
            df_stats = df_stats.append({'day':day_temp, 'day_patron':pair[0], 'day_earning':pair[1],
                'month':np.nan, 'month_patron':np.nan, 'month_earning':np.nan}, ignore_index=True)
            day_temp = day_temp - dateutil.relativedelta.relativedelta(days=1)
        df_stats['patreon_url'] = url
        df_stats['graphtreon_url'] = graphtreon_url
        df_stats['patrons'] = num_patron
        df_stats['amount'] = amount
        df_stats['goal'] = goal
        df_stats['percent_goal'] = percent_goal
        df_stats['creator_name'] = results[0]
        df_stats['launch_date'] = launch_date
    else:
        df_stats = df_stats.append({'patreon_url':url, 'graphtreon_url':graphtreon_url,
            'patrons':num_patron, 'amount':amount, 'goal':goal, 'percent_goal':percent_goal,
            'creator_name':np.nan, 'launch_date':launch_date,
            'day':np.nan, 'day_patron':np.nan, 'day_earning':np.nan,
            'month':np.nan, 'month_patron':np.nan, 'month_earning':np.nan}, ignore_index=True)
    return df_stats

if __name__ == "__main__":
    # Open csv file with a list of patreon urls
    df_patreon = pd.read_csv('files/20190711_github_patreon_url.csv')

    df_output = pd.DataFrame(columns=['patreon_url', 'graphtreon_url',
        'patrons', 'amount', 'goal', 'percent_goal', 'creator_name', 'launch_date',
        'day', 'day_patron', 'day_earning','month', 'month_patron', 'month_earning'])

    count = 0
    for url in tqdm(df_patreon['url'].values):
        if url is np.nan:
            continue
        elif url in urls:
            num_duplicates += 1
        else:
            urls.add(url)
            df_temp = get_stats(url)
            df_output = df_output.append(df_temp, ignore_index=True)
            count += 1

    print('Num duplicates:', num_duplicates)
    # df_output.to_csv('insert file name', index=False)
