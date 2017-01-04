#!/usr/bin/env python
import json, os, base64
import requests
import ConfigParser
import oauth2 as oauth, urllib

# Read the configuration
config = ConfigParser.ConfigParser()
config.read('config.ini')

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
        if 'media_id' not in content:
            raise ValueError

        return content['media_id']

    except ValueError:
        raise ValueError('No media ID returned')

