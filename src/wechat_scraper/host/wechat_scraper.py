import os
from wechat_scraper.host.utils import *
import requests
import re
import datetime
import urllib3
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import pandas as pd
import random
import argparse

DATE_TIME_PATTERN = re.compile(r'var create_time = "(\d+)"')
GLOBAL_PARAMS = None
ACCOUNT_NAME = ''
OFFSET = 0
COUNT = 0
DF_ARTICLE = None
CONTINUE_FLAG = 1
urllib3.disable_warnings()
params_path = os.path.join(os.path.dirname(__file__), '../virtualbox/params.json')
log_path = os.path.join(os.path.dirname(__file__), 'log.json')
offset_path = os.path.join(os.path.dirname(__file__), 'offset.json')
PASSWORD = 'secret'
VERBOSE = False

def get_params(reload = False):
    global GLOBAL_PARAMS
    global ACCOUNT_NAME
    global VERBOSE
    if os.path.exists(params_path):
        os.remove(params_path)
    if reload:
        refresh(ACCOUNT_NAME)
    if VERBOSE:
        print('Detecting...')
    while True:
        if os.path.exists(params_path):
            json_params = open(params_path, 'r', encoding = 'utf-8')
            params = json.load(json_params)
            GLOBAL_PARAMS = UserData.fromJson(params)
            json_params.close()
            if GLOBAL_PARAMS != None:
                print('Parameters detected')
                break
        time.sleep(1)

def initialize():
    global OFFSET
    global COUNT
    global GLOBAL_PARAMS
    global ACCOUNT_NAME
    OFFSET = 0
    COUNT = 0
    if os.path.exists(params_path):
        os.remove(params_path)
    get_params()
    ACCOUNT_NAME = get_account_name(GLOBAL_PARAMS)
    print(f'Start scraping {ACCOUNT_NAME}')


def get_links(user: UserData, tor = True):
    global CONTINUE_FLAG
    global PASSWORD
    url = f'https://mp.weixin.qq.com/mp/profile_ext?action=getmsg&f=json&count=10&is_ok=1&__biz={user.biz}&key={user.key}&uin={user.uin}&pass_ticket={user.pass_ticket}&offset={OFFSET}'
    session = get_tor_session(tor, PASSWORD)
    msg_json = session.get(url, headers=user_head(GLOBAL_PARAMS), verify=False).json()
    if (('can_msg_continue' in msg_json) and msg_json['can_msg_continue'] != 1):
        CONTINUE_FLAG = 0
    if 'general_msg_list' in msg_json.keys():
        url_list = json.loads(msg_json['general_msg_list'])['list']
        return url_list
    return []

def check_existing(article_detail: ArticleData):
    global DF_ARTICLE
    return((DF_ARTICLE['title'] == article_detail.title).any())

def parse_entry(user: UserData, article_detail: ArticleData, entry, tor = True):
    global OFFSET
    global COUNT
    global VERBOSE
    if 'app_msg_ext_info' in entry:
        entry = entry['app_msg_ext_info']
        #print(entry)
        flag = get_article(user, article_detail, entry, tor)
        if flag == 'LinkError':
            print(f'Link Error: {entry}')
        if flag == 'Scraped':
            if VERBOSE:
            print('Some articles have been scraped')
            return flag
        COUNT += 1
        if 'multi_app_msg_item_list' in entry:
            sublist = entry['multi_app_msg_item_list']
            if VERBOSE:
                print('Sub-articles detected')
            for item in sublist:
                flag = get_article(user, article_detail, item, tor)
                if flag == 'LinkError':
                    print(f'Link Error: {item}')
                COUNT += 1
    else:
        print('Scrape Error. No title')

def get_article(user: UserData, article_detail: ArticleData, entry, tor = True):
    global DF_ARTICLE
    if 'title' in entry:
        article_detail.title = entry['title']
        article_detail.link = entry['content_url'].replace('amp;', '')
        article_detail.author = entry['author']
    else:
        return('LinkError')
    if check_existing(article_detail):
        return('Scraped')
    try:
        get_content(article_detail, tor)
    except Exception as e:
        print(f'Scrape Content Error. Title: {entry['title']}, link: {entry['content_url'].replace('amp;', '')}, error message: {e}')
    try:
        get_stats(article_detail, user, tor)
    except Exception as e:
        print(f'Scrape Stats Error. Title: {entry['title']}, link: {entry['content_url'].replace('amp;', '')}, error message: {e}')
    DF_ARTICLE = pd.concat([DF_ARTICLE, pd.DataFrame([vars(article_detail)])], ignore_index=True)
    time.sleep(random.uniform(2,5))
    
def get_content(article_detail: ArticleData, tor = True):
    global PASSWORD
    session = get_tor_session(tor, PASSWORD)
    response = session.get(article_detail.link, headers=general_head, verify=False, timeout=(10, 10))
    soup = BeautifulSoup(response.text, 'html.parser')

    # get article content
    article_text = soup.find(id='js_content')
    
    if article_text is None:
        article_text = soup.find(id='page_content')
    
    if article_text is None:
        article_text = soup.find(id='page-content')

    if article_text:
        article_text = article_text.get_text()
        content = '\n'.join([text.strip() for text in article_text if text.strip()])
    
    article_detail.content = content

    # get article published date
    create_time = ''
    match = DATE_TIME_PATTERN.search(response.text)
    if match:
        timestamp = int(match.group(1))
        # Convert the timestamp to a datetime object
        create_time = datetime.datetime.fromtimestamp(timestamp)
    article_detail.pub_time = create_time

def get_stats(article_detail: ArticleData, user: UserData, tor = True):
    global PASSWORD
    session = get_tor_session(tor, PASSWORD)
    read_num, like_num = 0, 0
    query_params = parse_qs(urlparse(article_detail.link).query)
    mid = query_params['mid'][0]
    sn = query_params['sn'][0]
    idx = query_params['idx'][0]
    detailUrl = f'https://mp.weixin.qq.com/mp/getappmsgext?f=json&mock=&fasttmplajax=1&uin={user.uin}&key={user.key}&pass_ticket={user.pass_ticket}'
    response = session.post(detailUrl, headers=user_head(user),
                             data=article_data(user, mid, sn, idx), verify=False).json()
    if 'appmsgstat' in response:
        info = response['appmsgstat']
        read_num = info['read_num']
        like_num = info['old_like_num']
        article_detail.read = read_num
        article_detail.like = like_num
    article_detail.scrape_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def run(tor = True, daymax = 2000):
    global GLOBAL_PARAMS
    global OFFSET
    global COUNT
    global DF_ARTICLE
    global CONTINUE_FLAG
    global ACCOUNT_NAME
    start_time = time.time()
    initialize()
    
    if os.path.exists(log_path):
        with open(log_path, 'r') as log_file:
            scrape_log = json.load(log_file)
            if scrape_log['last_scrape'] != datetime.date.today().isoformat():
                scrape_log['last_scrape'] = datetime.date.today().isoformat()
                scrape_log['scrape_count'] = 0
                start_count = 0
            else:
                start_count = scrape_log['scrape_count']
    else:
        scrape_log = {
            'last_scrape': datetime.date.today().isoformat(),
            'scrape_count': 0
        }
        start_count = 0

    with open(offset_path, 'r', encoding='utf-8') as json_file:
        offset_dict = json.load(json_file)
    
    if ACCOUNT_NAME not in offset_dict:
        offset_dict[ACCOUNT_NAME] = 0
        offset_plus = 0
    else:
        offset_plus = offset_dict[ACCOUNT_NAME]

    data_path = os.path.join(os.path.dirname(__file__), '../data/{ACCOUNT_NAME}.csv')
    
    if os.path.exists(data_path):
        DF_ARTICLE = pd.read_csv(data_path, index_col=None)
    else:
        DF_ARTICLE = pd.DataFrame(columns = ['author', 'title', 'content', 'link', 'read', 'like', 'pub_time', 'scrape_time'])
    
    while True:
        url_list = get_links(GLOBAL_PARAMS, tor)
        # First error detection: automatic refresh
        if len(url_list) == 0:
            print('Reloading parameters, please wait...')
            get_params(reload = True)
            url_list = get_links(GLOBAL_PARAMS, tor)
            # Second error detection: manual refresh
            if len(url_list) == 0:
                input('Awaiting user action. Press any key to continue.')
                get_params()
                url_list = get_links(GLOBAL_PARAMS, tor)
                # Third error detection: break
                if len(url_list) == 0:
                    ('Parameter error, verify account status')
                    print(f'Article collection ended. {COUNT} articles collected.')
                    break
        first_overlap = True
        for entry in url_list:
            article_detail = ArticleData()
            flag = ''
            try:
                flag = parse_entry(GLOBAL_PARAMS, article_detail, entry, tor)
            except Exception as e:
                print(e)
                print(f'Scrape Error: {entry}')
            if flag == 'Scraped':
                if first_overlap:
                    first_overlap = False
                else:
                    OFFSET = OFFSET + offset_plus - 1
                    if offset_plus > 2:
                        offset_plus = 2
                        break
                    else: 
                        continue
            OFFSET += 1
            DF_ARTICLE.to_csv(data_path, index=False)
            offset_dict[ACCOUNT_NAME] = OFFSET
            with open(offset_path, 'w') as json_file:
                json.dump(offset_dict, json_file)
        if (scrape_log['scrape_count'] > daymax):
            print(f'Article collection completed. {COUNT} articles collected.')
            break
        if (CONTINUE_FLAG == 0):
            print(f'Article collection completed. {COUNT} articles collected.')
            break
        if VERBOSE:
            print(f'Time elapsed: {(time.time() - start_time):.2f} seconds, {COUNT} articles scraped')
        scrape_log['scrape_count'] = start_count + COUNT
        with open(log_path, 'w') as log_file:
            json.dump(scrape_log, log_file)
        time.sleep(random.uniform(2, 5))

def wechat_scraper(verbose = False, daymax = 2500):
    """
    Scrape WeChat data.
    
    Parameters:
    verbose (bool): If True, enable verbose mode. Default is False.
    daymax (int): Maximum number of days to scrape. Default is 2500.
    """
    global VERBOSE
    VERBOSE = verbose
    tor = input('Use Tor to avoid IP blocks (default is yes)? Y/n: ').upper()
    if (tor == 'N') or (tor == 'No'):
        tor = False
    else:
        tor = True
    run(tor, daymax)

def main():
    parser = argparse.ArgumentParser(description="WeChat Scraper Command-Line Interface")

    # Define command-line arguments
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode.')
    parser.add_argument('--daymax', type=int, default=2500, help='Maximum number of days to scrape. Default is 2500.')

    # Parse the arguments
    args = parser.parse_args()

    # Call the main function with parsed arguments
    wechat_scraper(verbose=args.verbose, daymax=args.daymax)

##################################################################
# Pipeline 
# 1. Set up mitmproxy to retrieve parameters in VirtualBox (retrieve_params.py)
# 2. Initialize (initialize()) and get parameters(get_params())
# 3. Start retrieving article links (get_links())
# 4. For each entry in the links list, retrieve article information (parse_entry()), data saved in the ArticleData class
# 5. After each iteration, save article data into csv file for maximum record retention

if __name__ == '__main__':
    main()
    
