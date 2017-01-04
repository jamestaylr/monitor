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

""" Gets products from a url returning a single product or array of products
"""
def get_products(url, limit):
    payload = {'limit': limit}
    r = requests.get(url, params=payload)

    if r.status_code != 200:
        print 'Handling a {} status code'.format(r.status_code)
        r.raise_for_status()

    json = r.json()
    products = sorted(json['products'], key=lambda x: x['published_at'], reverse=True)
    return products if len(products) != 1 else products[0]

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

# Check the content from the subscribed sites
sites = json.loads(open('data.json').read())['sites']
for site in sites:
    print 'Processing site', site['name']

    # Get the most recently published product
    try:
        current = get_products(site['url'], 1)
    except requests.exceptions.HTTPError:
        print 'Processing site {} failed'.format(site['name'])
        continue

    lock_filename = 'locks/{}.lock'.format(site['name'])
    try:
        previous = open(lock_filename, 'r').read().split()
        # Compare to the lock
        if current['id'] == int(previous[0]):
            continue
    except IOError:
        # Lock on the current product does not exist, recreate the lock
        if not os.path.exists(os.path.dirname(lock_filename)):
            try:
                os.makedirs(os.path.dirname(lock_filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(lock_filename, 'w') as lock:
            lock.write('{} {}'.format(current['id'], current['published_at']))
        print 'Creating new lock file {}'.format(lock_filename)
        continue

    # Report on newly published products
    try:
        n = config.get('monitor', 'delta_requests')
        for product in get_products(site['url'], n):
            if product['id'] == int(previous[0]):
                break

            media_id = None
            link = '{}{}'.format(site['base_handle'], product['handle'])
            link = link.encode('ascii', 'ignore')

            try:
                if len(product['images']) > 0:
                    media_id = upload_media(product['images'][0]['src'])
            except ValueError:
                print e

            tweet('{} {}'.format(
                product['title'],
                link
            ), media_id)

    except requests.exceptions.HTTPError:
        print 'Processing site {} failed'.format(site['name'])
        continue

    # Update the lock
    with open(lock_filename, 'w') as lock:
        lock.write('{} {}'.format(current['id'], current['published_at']))

