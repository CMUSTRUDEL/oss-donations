# Get the urls associated with the detected funding services
# from a list of slugs
from urllib.request import Request, urlopen
import pandas as pd
import numpy as np
import re
from tqdm import tqdm
import time
import requests

services = {
            'opencollective' : ['opencollective.com/'],
            'kickstarter' : ['kickstarter.com/'],
            'patreon' : ['patreon.com/'],
            'salt': ['salt.bountysource.com/'],
            'tidelift': ['tidelift.com/subscription/'],
            'otechie': ['otechie.com/'],
            'bountysource': ['bountysource.com/'],
            'flattr': ['flattr.com/'],
            'issuehunt': ['issuehunt.io/'],
            'liberapay': ['liberapay.com/', 'gratipay.com/'],
            'paypal': ['paypal.com/', 'paypal.me/'],
            'tip4commit': ['tip4commit.com/']
        }

def get_url(pair):
    (slug, service, sha) = pair
    try:
        keywords = services[service]
    except:
        return None
    url = 'https://github.com/'+slug+'/tree/'+sha
    try:
        webpage = requests.get(url).text
    except:
        return None

    if service == 'opencollective':
        # Looks for spaces, [ ], ', ", ., ( ), < >, |, { }, /, \
        regex = re.compile('[\[\'\".()<>/\|}{\s\]\\\]')
    else:
        # Looks for spaces, [ ], ', ", ., ( ), < >, |, { }
        regex = re.compile('[\[\'\".()<>\|}{\s\]]')

    for keyword in keywords:
        # find first instance of keyword
        index = webpage.find(keyword)
        if index != -1:
            regex_index = regex.search(webpage[index+len(keyword):]).span()
            end_index = regex_index[0]+index+len(keyword)
            # get https:// or http://
            start_index1 = webpage.rfind('https://', 0, index)
            start_index2 = webpage.rfind('http://', 0, index)
            if start_index1 > start_index2:
                funding_url = webpage[start_index1:end_index]
            else:
                funding_url = webpage[start_index2:end_index]
            # Make sure there is stuff after .com
            if funding_url.find(keyword.split('.')[-1]) == (len(funding_url)-4):
                return None
            # Make sure url does not contain special characters
            regex = re.compile('[\[\'\"()<>\|}{\s\]]')
            if regex.search(funding_url) is None:
                return funding_url
        continue
    return None

if __name__ == "__main__":
    start = time.time()
    errors = []
    df_contains_bePatron = pd.DataFrame(columns=['slug', 'service', 'filename', 'url'])
    # make new DataFrame
    df_url = pd.DataFrame(columns=['slug', 'service', 'filename', 'url'])
    # open CSV file with relevant slugs
    df_data = pd.read_csv('insert file name')
    # go through rows and get url
    for index in tqdm(list(df_data.index.values)[:]):
        row = df_data.loc[index]
        slug = row.slug
        service = row.service
        sha = row.sha
        name = row['filename']
        url = get_url((slug, service, sha))
        if url is None:
            errors.append(slug)
        elif service == 'patreon' and 'bePatron' in url:
            df_contains_bePatron = df_contains_bePatron.append({'slug':slug,
                'service':service, 'filename':name, 'url':url},
                ignore_index=True, sort=False)
        else:
            df_url = df_url.append({'slug':slug,
                'service':service, 'filename':name, 'url':url},
                ignore_index=True, sort=False)

    # save to CSV
    df_url.to_csv('insert file name', index=False)
    df_contains_bePatron.to_csv('insert file name', index=False)
    pd.Series(errors, name='error').to_csv('insert file name', header=True, index=False)
    end = time.time()
    print(end-start) # Gives time in seconds
