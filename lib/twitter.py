#!/usr/bin/env python
import json, os, base64
import requests
import ConfigParser
import oauth2 as oauth, urllib

import __main__
config = __main__.config

""" Posts a tweet
"""
def tweet(status_string, media_id):
    if not config.getboolean('twitter', 'should_tweet'):
        print 'Abort posting tweet'
        return

    # Build the OAuth client
    consumer = oauth.Consumer(
            key=config.get('twitter', 'consumer_key'),
            secret=config.get('twitter', 'consumer_secret')
        )
    token = oauth.Token(
            key=config.get('twitter', 'access_token'),
            secret=config.get('twitter', 'access_secret')
        )
    client = oauth.Client(consumer, token)

    data = {
        'status': status_string,
        'trim_user': 'true'
    }
    if media_id is not None:
        data['media_ids'] = media_id

    # Send the request
    resp, content = client.request(
            'https://api.twitter.com/1.1/statuses/update.json',
            method='POST',
            body=urllib.urlencode(data),
            headers=None
        )

    try:
        content = json.loads(content)
        print 'Posted tweet with status', resp.status, (content['id']
            if resp.status == 200
                else [ str(error['message']) for error in content['errors'] ])
    except ValueError:
        pass

""" Uploads an image URL to Twitter for use in a status
"""
def upload_media(link):
    r = requests.get(link)

    # Build the OAuth client
    consumer = oauth.Consumer(
            key=config.get('twitter', 'consumer_key'),
            secret=config.get('twitter', 'consumer_secret')
        )
    token = oauth.Token(
            key=config.get('twitter', 'access_token'),
            secret=config.get('twitter', 'access_secret')
        )
    client = oauth.Client(consumer, token)

    # Send the request
    resp, content = client.request(
            'https://upload.twitter.com/1.1/media/upload.json',
            method='POST',
            body=urllib.urlencode({
                'media_data': base64.b64encode(r.content),
            }),
            headers=None
        )

    try:
        content = json.loads(content)
        if not 'media_id' in content:
            print ('Error adding media',
                    [ str(error['message']) for error in content['errors'] ])
            raise ValueError

        return content['media_id']

    except ValueError:
        raise ValueError('No media ID returned')

def send_dm(text, user_handle=None):
    # Build the OAuth client
    consumer = oauth.Consumer(
            key=config.get('twitter', 'consumer_key'),
            secret=config.get('twitter', 'consumer_secret')
        )
    token = oauth.Token(
            key=config.get('twitter', 'access_token'),
            secret=config.get('twitter', 'access_secret')
        )
    client = oauth.Client(consumer, token)

    # Send the request
    resp, content = client.request(
            'https://api.twitter.com/1.1/direct_messages/new.json',
            method='POST',
            body=urllib.urlencode({
                'text': text,
                'user_id': (config.get('twitter', 'user_id')
                        if user_handle is None
                        else user_handle
                    )
            }),
            headers=None
        )

def has_been_tweeted(match):
    # Build the OAuth client
    consumer = oauth.Consumer(
            key=config.get('twitter', 'consumer_key'),
            secret=config.get('twitter', 'consumer_secret')
        )
    token = oauth.Token(
            key=config.get('twitter', 'access_token'),
            secret=config.get('twitter', 'access_secret')
        )
    client = oauth.Client(consumer, token)

    params=urllib.urlencode({
        'count': config.get('twitter', 'tweet_duplicate_check'),
        'trim_user': 'true'
    })

    resp, content = client.request(
            'https://api.twitter.com/1.1/statuses/user_timeline.json?{}'.format(params),
            method='GET',
            headers=None
        )

    try:
        tweets = json.loads(content)
        last = tweets[len(tweets) - 1]

        for tweet in tweets:
            if match in tweet['text']:
                return True, last
        return False, last
    except ValueError:
        return False

