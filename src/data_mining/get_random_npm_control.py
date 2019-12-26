# Get a random sample of npm projects for control group
import pandas as pd
import random

if __name__ == "__main__":
    # Open funding_slugs.csv and get slug names
    slugs = pd.read_csv('files/20190614_funding_slugs.csv', header=None)
    slugs.columns = ['slug']
    slugs_lst = slugs['slug'].values

    # Open list of npm slugs
    lines = [line.rstrip('\n') for line in open('files/20190702_npm_slugs.txt', encoding='utf8', errors='ignore')]

    num_slugs = len(lines)
    num_control = 10000

    control_group = []
    counter = 0

    # Generate random number between 0 and num_slugs - 1
    # If slug is not already selected and doesn't have a funding service,
    # then add to control_group
    while counter < 3000:
        random_num = random.randint(0,num_slugs)
        random_slug = lines[random_num]
        if random_slug not in slugs_lst:
            control_group.append(random_slug)
            counter += 1

    print(len(control_group))

    # Save control_group to CSV
    # pd.Series(control_group, name='slug').to_csv('insert file name', header=True, index=False)
