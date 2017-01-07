#!/usr/bin/env python
import json, os, base64, sys
import requests
import oauth2 as oauth, urllib

# Read the configuration
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('config.ini')

from lib import twitter

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

# Check the content from the subscribed sites
sites = json.loads(open('bin/shopify.json').read())['sites']
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

            if twitter.has_been_tweeted(product['title']):
                print 'Not posting duplicated tweet for', product['handle']
                continue

            media_id = None
            link = '{}{}'.format(site['base_handle'], product['handle'])
            link = link.encode('ascii', 'ignore')

            try:
                if len(product['images']) > 0:
                    media_id = twitter.upload_media(product['images'][0]['src'])
            except ValueError:
                print e

            twitter.tweet('{} {}'.format(
                product['title'],
                link
            ), media_id)

    except requests.exceptions.HTTPError:
        print 'Processing site {} failed'.format(site['name'])
        continue

    # Update the lock
    with open(lock_filename, 'w') as lock:
        lock.write('{} {}'.format(current['id'], current['published_at']))

