# This script goes through the scraped OpenCollective transaction
# files and gets the first transaction and expense dates
import os
import pandas as pd
import numpy as np
from datetime import datetime
from tqdm import tqdm

errors = []

def convert_datetime(x):
    try:
        temp = datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            temp = datetime.strptime(x, '%m/%d/%Y %H:%M')
        except:
            temp = datetime.strptime(x, '%m/%d/%Y %H:%M:%S')
    return temp

if __name__ == "__main__":
    # Open CSV that contains a list of opencollective urls
    df_data = pd.read_csv('files/20190727_asking_all.csv')
    df_sub = df_data[df_data.opencollective==1].copy()
    df_sub['first_date'] = np.nan
    df_sub['first_expense_date'] = np.nan
    # Get list of urls with opencollective
    urls = list(set(df_sub.opencollective_url.dropna().values))
    names = [url.split('#')[0].rstrip() for url in urls]
    names = [name.split('/')[-1] for name in names]
    names = [name.split(' ')[0] for name in names]
    url_dict = dict(zip(names, urls))
    # Go through scraped files
    path = 'files/20190719_OpenCollective CSV'
    directory = os.fsencode(path)
    for file in tqdm(os.listdir(directory)):
        # Open csv file
        file = file.decode("utf-8")
        df_oc = pd.read_csv(path+'/'+file)
        name = file.split('--')[0]
        matches = [x for x in names if name == x.lower()]
        if len(matches) < 1:
            errors.append(name)
        else:
            # Get data from df_oc (already sorted by date)
            df_oc = df_oc.iloc[::-1]
            first_date = df_oc.iloc[0]['Transaction Date']
            first_expense_date = np.nan
            for index, row in df_oc.iterrows():
                if row['Transaction Amount'] < 0:
                    first_expense_date = row['Transaction Date']
            for match in matches:
                # Update df_data
                for index, row in df_sub[df_sub.opencollective_url==url_dict[match]].iterrows():
                    df_sub.loc[index, 'first_date'] = first_date
                    df_sub.loc[index, 'first_expense_date'] = first_expense_date

    df_sub.to_csv('insert file name', index=False, columns=['slug', 'first_date', 'first_expense_date'])
    pd.Series(errors, name='error').to_csv('insert file name', header=True, index=False)
