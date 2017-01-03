#!/usr/bin/env python
import json
import requests
import ConfigParser
import oauth2 as oauth, urllib

# Read the configuration
config = ConfigParser.ConfigParser()
config.read('config.ini')

""" Posts a tweet
"""
def tweet(status_string):
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

    # Send the request
    resp, content = client.request(
            'https://api.twitter.com/1.1/statuses/update.json',
            method='POST',
            body=urllib.urlencode({
                'status': status_string,
                'trim_user': 'true'
            }),
            headers=None
        )
    content = json.loads(content)
    print resp.status, (content['id'] if resp.status == 200
            else [ str(error['message']) for error in content['errors'] ])

