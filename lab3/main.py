import json
import datetime
import os
import smtplib
import logging as log
from time import sleep
from urllib.parse import urlencode, urlunparse
import csv
import requests
from abc import ABCMeta
from abc import abstractmethod
from bs4 import BeautifulSoup


keyword = "love"


class TwitterSearch(object):

    __meta__ = ABCMeta

    def __init__(self, rate_delay, error_delay=5):
        self.rate_delay = rate_delay
        self.error_delay = error_delay

    def search(self, query):
        url = self.construct_url(query)
        min_tweet = None
        response = self.execute_search(url)
        write_f = open('tweets.csv', 'a', encoding='utf-8', newline='')
        while response is not None and response['items_html'] is not None:
            tweets = self.parse_tweets(response['items_html'])

            if len(tweets) == 0:
                break

            if min_tweet is None:
                min_tweet = tweets[0]

            self.save_tweets(tweets, write_f)
            max_tweet = tweets[-1]
            if min_tweet['tweet_id'] is not max_tweet['tweet_id']:
                if "min_position" in response.keys():
                    max_position = response['min_position']
                else:
                    max_position = "TWEET-%s-%s" % (max_tweet['tweet_id'], min_tweet['tweet_id'])
                url = self.construct_url(query, max_position=max_position)
                sleep(self.rate_delay)
                response = self.execute_search(url)

        write_f.close()

    def execute_search(self, url):
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.'
                              '86 Safari/537.36'
            }
            req = requests.get(url, headers=headers)
            data = json.loads(req.text)
            return data
        except Exception as e:
            log.error(e)
            log.error("Sleeping for %i" % self.error_delay)
            sleep(self.error_delay)
            return self.execute_search(url)

    @staticmethod
    def parse_tweets(items_html):
        soup = BeautifulSoup(items_html, "html.parser")
        tweets = []
        for li in soup.find_all("li", class_='js-stream-item'):

            if 'data-item-id' not in li.attrs:
                continue

            tweet = {
                'tweet_id': li['data-item-id'],
                'text': None,
                'user_id': None,
                'user_screen_name': None,
                'user_name': None,
                'created_at': None,
                'retweets': 0,
                'favorites': 0
            }

            text_p = li.find("p", class_="tweet-text")
            if text_p is not None:
                tweet['text'] = text_p.get_text()

            user_details_div = li.find("div", class_="tweet")
            if user_details_div is not None:
                tweet['user_id'] = user_details_div['data-user-id']
                tweet['user_screen_name'] = user_details_div['data-screen-name']
                tweet['user_name'] = user_details_div['data-name']

            date_span = li.find("span", class_="_timestamp")
            if date_span is not None:
                tweet['created_at'] = datetime.datetime.fromtimestamp(float(date_span['data-time-ms'])/1000)

            retweet_span = li.select("span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
            if retweet_span is not None and len(retweet_span) > 0:
                tweet['retweets'] = int(retweet_span[0]['data-tweet-stat-count'])

            favorite_span = li.select("span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
            if favorite_span is not None and len(retweet_span) > 0:
                tweet['favorites'] = int(favorite_span[0]['data-tweet-stat-count'])

            tweets.append(tweet)
        return tweets

    @staticmethod
    def construct_url(query, max_position=None):
        params = {
            # Type Param
            'f': 'tweets',
            # Query Param
            'q': query
        }
        if max_position is not None:
            params['max_position'] = max_position

        url_tuple = ('https', 'twitter.com', '/i/search/timeline', '', urlencode(params), '')

        return urlunparse(url_tuple)

    @abstractmethod
    def save_tweets(self, tweets, write_f):
        """Save tweets like you want"""


class TwitterSearchImpl(TwitterSearch):

    def __init__(self, rate_delay, error_delay):
        super(TwitterSearchImpl, self).__init__(rate_delay, error_delay)
        self.key_freq = 0
        self.first_write = True

    def save_tweets(self, tweets, write_f):
        dict_writer = csv.DictWriter(write_f, tweets[0].keys())

        if self.first_write and os.stat("tweets.csv").st_size == 0:
            dict_writer.writeheader()
            self.first_write = False
        dict_writer.writerows(tweets)

        self.key_freq += count_key(tweets, keyword)


def count_key(tweets, keyword):
    counter = 0
    for tweet in tweets:
        counter += tweet['text'].lower().count(keyword)

    return counter


def notification(key_freq, keyword, since, until):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("twitter.notification.mail@gmail.com", "")
    msg = "Keyword '{}' has been found {} times.\nTimeline: from {} to {}".format(keyword,
                                                                                   key_freq,
                                                                                   since,
                                                                                   until)
    server.sendmail("twitter.notification.mail@gmail.com", "kirill.kiforchuk@gmail.com", msg)
    print("Mail notification has been sent")
    server.quit()


def last_date(date):
    with open("date.txt", 'a') as file:
        file.write(date)

    file.close()


if __name__ == '__main__':
    datefile = open("date.txt", 'r+')
    query = ""
    author = "urbandictionary"
    since = datetime.datetime.strptime(datefile.readlines()[-1], '%Y-%m-%d')
    until = since + datetime.timedelta(days=1)
    query = "%s from:%s since:%s until:%s" % (query,
                                              author,
                                              str(datetime.datetime.date(since)),
                                              str(datetime.datetime.date(until)))
    datefile.writelines('\n'+until.strftime('%Y-%m-%d'))
    datefile.close()
    rate_delay_seconds = 0
    error_delay_seconds = 5
    twit = TwitterSearchImpl(rate_delay_seconds, error_delay_seconds)
    twit.search(query)
    print("Keyword {} has been found {} times.\nTimeline: from {} to {}".format(keyword,
                                                                                twit.key_freq,
                                                                                since,
                                                                                until))
    if twit.key_freq != 0:
        notification(twit.key_freq, keyword, since, until)
