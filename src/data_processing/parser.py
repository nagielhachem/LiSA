import os, errno

try:
    import json
except ImportError:
    import simplejson as json

from twitterscraper import query_tweets, Tweet
import datetime
import numpy as np



def check_cache(filename, directory, max_size_bytes):
    size = 0
    filenames = os.listdir(directory)
    for f in filenames :
        f = directory + '/' + f
        if os.path.isfile(f) :
            s = os.path.getsize(f)
            size += s
    print('Cache size : ' + str(size) + ' bytes (max : ' + str(max_size_bytes) + ' bytes)')
    if size > max_size_bytes :
        delta = size - max_size_bytes
        cleaned = 0
        for f in sorted(filenames, key=lambda f: os.path.getmtime(directory + '/' + f)) :
            f = directory + '/' + f
            if f != filename :
                file_time = os.path.getmtime(f)
                file_size = os.path.getsize(f)
                try:
                    os.remove(f)
                    cleaned += file_size
                    if cleaned >= delta :
                        print(str(cleaned) + ' bytes cleaned')
                        break
                except OSError as e:
                    print(e)
    print()

def get_query_str(subject, since, until, near = None, limit = None):
    """
    Returns the query string that twitter scrapper accepts

    Params:
        :subject -- str: subject of tweet ("Trump OR Nagi")
        :since   -- str: fetch tweets since that date ("2017-11-30")
        :until   -- str: fetch tweets until that date ("2017-12-04")
        :near    -- str: fetch tweets published near that location ("New York")
        :limit   -- int: minimum number of tweets to fetch (1000)

    Return:
        :query -- str>: query sring
    """

    since_date = datetime.datetime.strptime(since, '%Y-%m-%d')
    #since_date += datetime.timedelta(days=-1)
    until_date = datetime.datetime.strptime(until, '%Y-%m-%d')
    until_date += datetime.timedelta(days=1)
    since = since_date.strftime('%Y-%m-%d')
    until = until_date.strftime('%Y-%m-%d')
    query = ""
    query += subject
    if near is not None:
        query += " near:" + near.replace(' ', '')
    query += " since:" + since
    query += " until:" + until
    return query

def fetch_tweets(subject, since, until, near = None, limit = None):
    """
    Returns tweets matching parameters

    Params:
        :subject -- str: subject of tweet ("Trump OR Nagi")
        :since   -- str: fetch tweets since that date ("2017-11-30")
        :until   -- str: fetch tweets until that date ("2017-12-04")
        :near    -- str: fetch tweets published near that location ("New York")
        :limit   -- int: minimum number of tweets to fetch (1000)

    Return:
        :tweets -- list<twitterscrapper.Tweet>: tweets that match description
    """

    query = get_query_str(subject, since, until, near, limit)
    print('QUERY : ' + query + " limit: " + str(limit))
    return query_tweets(query, limit)

def create_tweet(text, date_time) :
    return Tweet(timestamp=date_time, text=text, user='', fullname='', id='', url='', replies='', retweets='', likes='')

def fetch_and_save_tweets(filename, subject, since, until, near = None, limit = None):
    """
    Fetch tweets matching description and save them into file

    Params:
        :filename -- str: file path in which queries will be saved  ("output.json")
        :subject  -- str: subject of tweet ("Trump OR Nagi")
        :since    -- str: fetch tweets since that date ("2017-11-30")
        :until    -- str: fetch tweets until that date ("2017-12-04")
        :near     -- str: fetch tweets published near that location ("New York")
        :limit    -- int: minimum number of tweets to fetch (1000)

    Return:
        None
    """

    print('-------------')
    date_format = '%Y-%m-%d'
    subject = subject.lower()
    limit = int(limit)
    if near is not None:
        near = near.lower()
    filename = '.cache/' + subject + '_' + near + '.json'
    if not(os.path.isdir('.cache')):
        os.makedirs('.cache/')
    check_cache(filename, '.cache', 1000000000)

    since_date = datetime.datetime.strptime(since, date_format)
    until_date = datetime.datetime.strptime(until, date_format)
    if since_date > until_date :
       tmp_date = since_date
       since_date = until_date
       until_date = tmp_date
       tmp = since
       since = until
       until = tmp
    since_date1 = since_date
    until_date1 = until_date
    since_date_double = None
    until_date_double = None

    since_json = since
    until_json = until

    tweets = []
    do_fetch = True
    between = False
    json_tweets = []
    # Remove file with same filename if exists
    if os.path.isfile(filename) :
        json_file = open(filename, 'r')
        json_data = json.load(json_file)
        since2 = json_data['query']['since']
        since_date2 = datetime.datetime.strptime(since2, date_format)
        until2 = json_data['query']['until']
        until_date2 = datetime.datetime.strptime(until2, date_format)

        json_tweets = json_data['tweets']
        json_tweets.reverse()
        nb_cached = len(json_tweets)
        print(str(nb_cached) + ' tweets in cache for this query')

        if until_date >= since_date2 and until_date < until_date2 :
            between = True
            count = 0
            for tweet in json_tweets :
                timestamp = tweet['timestamp']
                date_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                if date_time < since_date :
                    break
                if date_time < until_date :
                    if count < limit :
                        t = create_tweet(tweet['text'], date_time)
                        tweets.append(t)
                        count += 1
                    else :
                        do_fetch = False
                        break
            until_date1 = since_date2
            until_date1 += datetime.timedelta(days=-1)
            until_json = until2
            print('(1) Loaded ' + str(count) + ' tweets from cache')
        if since_date <= until_date2 and since_date > since_date2 :
            between = True
            since_date1 = until_date2
            since_json = since2
        if not between :
            if until_date == until_date2 and since_date == since_date2 :
                count = 0
                date_time = None
                for tweet in json_tweets :
                    timestamp = tweet['timestamp']
                    date_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    if count < limit :
                        t = create_tweet(tweet['text'], date_time)
                        tweets.append(t)
                        count += 1
                    else :
                        do_fetch = False
                        break
                if count == limit :
                    do_fetch = False
                if date_time is not None :
                    until_date1 = datetime.datetime.strptime(date_time.strftime(date_format), date_format)
            elif until_date < since_date2 :
                since_json = since
            elif since_date > until_date2 :
                until_json = until
            else :
                since_date_double = since_date1
                until_date_double = since_date2
                until_date_double += datetime.timedelta(days=-1)
                since_date1 = until_date2
                since_date1 += datetime.timedelta(days=1)
                since_json = since_date_double.strftime(date_format)
                until_json = until_date1.strftime(date_format)

    if until_date1 < since_date1 :
        do_fetch = False
        print('- Unnecessary to fetch -')
        return tweets

    since = since_date1.strftime(date_format)
    until = until_date1.strftime(date_format)

    to_save = []
    # fetch tweets and add them to dic
    limit = limit - len(tweets)
    query_tweets = fetch_tweets(subject, since, until, near, limit)
    query_tweets.reverse()
    print('(1) Downloaded ' + str(len(query_tweets)) + ' new tweets')
    fetched_tweets = []
    i = 0
    last_date = None
    if tweets :
        last_date = tweets[-1].timestamp
    else :
        last_date = until_date1 + datetime.timedelta(days=1)
    for tweet in query_tweets:
        if i < limit :
            if tweet.timestamp < last_date :
                tweets.append(tweet)
                fetched_tweets.append(tweet)
                i += 1
        else :
            break
    if not tweets :
        to_save.extend(fetched_tweets)
        to_save.extend(dict_to_tweets(json_tweets))
    else :
        to_save.extend(dict_to_tweets(json_tweets))
        to_save.extend(fetched_tweets)
    if tweets :
        last_date = tweets[-1].timestamp
    else :
        last_date = until_date1 + datetime.timedelta(days=1)
    if between :
        count = len(tweets)
        i = 0
        for tweet in json_tweets :
            timestamp = tweet['timestamp']
            date_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            if date_time < since_date :
                break
            if date_time < until_date :
                if count < limit :
                    if date_time < last_date :
                        t = create_tweet(tweet['text'], date_time)
                        tweets.append(t)
                        count += 1
                        i += 1
                else :
                    break
        print('(2) Loaded ' + str(i) + ' tweets from cache')
 
    if since_date_double is not None :
        count = len(tweets)
        to_add = limit - count
        i = 0
        for tweet in json_tweets :
            if i < to_add :
                timestamp = tweet['timestamp']
                date_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                if date_time < last_date :
                    t = create_tweet(tweet['text'], date_time)
                    tweets.append(t)
                    i += 1
            else :
                break
        print('(2) Loaded ' + str(i) + ' tweets from cache')

        limit = limit - len(tweets)
        query_tweets = fetch_tweets(subject, since_date_double.strftime(date_format), until_date_double.strftime(date_format), near, limit)
        query_tweets.reverse()
        last_date = tweets[-1].timestamp
        print('(2) Downloaded ' + str(len(query_tweets)) + ' new tweets')
        i = 0
        for tweet in query_tweets:
            if i < limit :
                if tweet.timestamp < last_date :
                    tweets.append(tweet)
                    to_save.append(tweet)
                    i += 1

    to_save.reverse()
    filename = '.cache/' + subject + '_' + near + '.json'
    save_tweets(filename, subject, near, since_json, until_json, to_save)

    return tweets

def read_json_folder(folder):
    """
    Reads a directory containing json files and returns data as a dictionary

    Params:
        :folder -- str :  folder path to read from
    """
    for root, subFolders, files in os.walk(rootdir):
        data = []
        for file in files:
            Doc = open(os.path.join(root,file), "r").readline()
            data +=  json.loads(Doc)
    return data

def tweets_to_dict(tweets):
    to_save = []
    for tweet in tweets:
        t = {}
        t['text'] = tweet.text
        t['timestamp'] = str(tweet.timestamp)
        to_save.append(t)
    return to_save

def dict_to_tweets(dics):
    tweets = []
    for dic in dics :
        text = dic['text']
        timestamp = dic['timestamp']
        date_time = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        t = create_tweet(text, date_time)
        tweets.append(t)
    return tweets

def save_tweets(filepath, subject, near, since, until, tweets) :
    """
    Params:
        :subject  -- str: subject of tweet ("Trump OR Nagi")
        :near     -- str: fetch tweets published near that location ("New York")
        :since    -- str: fetch tweets since that date ("2017-11-30")
        :until    -- str: fetch tweets until that date ("2017-12-04")
        :tweets   -- list<Tweet>: tweets to save

    Return:
        None
    """
    # save query into JSON
    query = {}
    query['subject'] = subject
    query['near'] = near
    query['since'] = since
    query['until'] = until
    
    # add JSON query to main JSON
    data = {}
    data['query'] = query
    data['tweets'] = tweets_to_dict(tweets)
    
    # save tweets into file as json
    if type(filepath) is str: 
        file = open(filepath, 'w')
    else:
        file = filepath
    file.write(json.dumps(data))
    file.close()

def read_tweets(filepath):
    """
    Reads only tweets from file

    Params:
        :filename -- str: file path to read from

    Return:
        :tweets -- np.array: array containing all tweets in file
    """
    f = open(filepath)
    data = json.load(f)
    f.close()
    return data['query'], np.array(dict_to_tweets(data['tweets']))
