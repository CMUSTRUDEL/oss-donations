# This script can be used to download all of the
# transaction csv files from a list of opencollective urls
# It creates the 20190719_OpenCollective CSV folder, which is used in other scripts.
from splinter import Browser
from bs4 import BeautifulSoup
from time import sleep
import pandas as pd
import numpy as np
from tqdm import tqdm

# Make sure that no duplicate urls are searched
urls = set()
num_duplicates = 0
errors = []
no_transactions = []

def download_csv(browser, url):
    try:
        # Go to opencollective webpage
        browser.visit(url)
    except:
        errors.append(url)
        return None

    try:
        # Click the download csv button
        buttons = browser.find_by_text('Download CSV')
        for button in buttons:
            button.click()

        sleep(1)
        # Fill in the start date
        browser.find_by_css('input[value="06/01/2019"]').fill('05/01/2000')
        sleep(2)

        # Click the download button
        buttons = browser.find_by_text('Download')
        for button in buttons:
            button.click()

        sleep(7)
        return None

    except:
        # Check if there are no transactions
        try:
            result = browser.find_by_text('No transactions')
            if result:
                no_transactions.append(url)
            else:
                errors.append(url)
            return None

        except:
            errors.append(url)
            return None


if __name__ == "__main__":
    # Open csv file with a list of opencollective urls
    df_oc = pd.read_csv('files/20190711_github_opencollective_url.csv')

    # Open up a Chrome browser the file path varies depending on where your chromedriver is located
    executable_path = {'executable_path':'C:\Program Files\chromedriver.exe'}
    browser = Browser('chrome', **executable_path)
    # sleep(5)

    # Set settings (download location) and then press 'Enter'
    input("Press Enter to continue...")

    # Go through each row
    count = 0
    for url in tqdm(df_oc['url'].values[:]):
        if url is np.nan:
            continue
        # remove #
        if '#' in url:
            url = url.split('#')[0]
        url = url+'/transactions'
        # Check to make sure url is unique
        if url in urls:
            num_duplicates += 1
        else:
            urls.add(url)
            download_csv(browser, url)
            count += 1
    sleep(5)
    browser.quit()
    print('Num duplicates:', num_duplicates)
    print('Errors:', errors)
    print('Nothing:', no_transactions)

    # pd.Series(errors, name='error').to_csv('insert file name', header=True, index=False)
    # pd.Series(no_transactions, name='no_transactions').to_csv('insert file name', header=True, index=False)
