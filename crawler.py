#!/usr/bin/env python
import requests
import xmltodict
import hashlib
import json, os
from datetime import datetime
from dateutil import parser

# Read the configuration
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('config.ini')

from lib import twitter

""" Checks to see if a given product is duplicated in a site datafile
"""
def is_duplicate(product, name):
    # Open the data file
    dat_filename = 'locks/{}.dat'.format(name)
    import mmap
    try:
        f = open(dat_filename)
        if os.path.getsize(dat_filename) == 0:
            return False
    except IOError:
        return False

    s = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    return True if s.find(product) != -1 else False

# Open the filter file
with open('bin/filter.dat') as f:
    keywords = [x.strip('\n') for x in f.readlines()]
filter = [' {}'.format(x) for x in keywords] + ['{} '.format(x) for x in keywords]

# Iterate through the sites
sites = json.loads(open('bin/sitemap.json').read())['sites']
for site in sites:
    print 'Processing site', site['name']

    # Query the sitemap
    try:
        r = requests.get(site['url'], timeout=10)
    except requests.exceptions.HTTPError:
        print 'Processing site {} failed'.format(site['name'])
        continue

    # Parse the sitemap
    data = xmltodict.parse(r.content, dict_constructor=dict)
    products = sorted(data['urlset']['url'],
            key=lambda x: ('lastmod' not in x,
                x.get('lastmod', None)),
            reverse=True)

    products = [d for d in products if 'lastmod' in d]
    first = products[0]

    lock_filename = 'locks/{}.lock'.format(site['name'])
    try:
        previous = open(lock_filename, 'r').read().split()
    except IOError:
        # Lock on the current product does not exist, recreate the lock
        if not os.path.exists(os.path.dirname(lock_filename)):
            try:
                os.makedirs(os.path.dirname(lock_filename))
            except OSError as exc: # Guard against race condition
                if exc.errno != errno.EEXIST:
                    raise
        with open(lock_filename, 'w') as lock:
            first_id = hashlib.sha224(first['loc']).hexdigest()
            lock.write('{} {}'.format(first_id, first['lastmod']))
        print 'Creating new lock file {}'.format(lock_filename)
        continue

    # Iterate through the products
    tweet_count = 0
    for product in products:
        id = hashlib.sha224(product['loc']).hexdigest()
        try:
            if id == previous[0]:
                break
        except IndexError:
            # Problem with the lock file, recreate the lock
            with open(lock_filename, 'w') as lock:
                lock.write('{} {}'.format(id, product['lastmod']))
            print 'Recreating lock file {}'.format(lock_filename)
            continue

                # Apply the keyword filter
        try:
            title = product['image:image']['image:title'].lower()

            brands = ['adidas', 'jordan', 'nike', 'nmd', 'yeezy', 'ultraboost', 'pk']
            t = title.lower().replace(' ', '')
            if not any(x in t for x in brands):
                print 'No brand keywords in', product['loc']
                continue

            if any(x in title for x in filter):
                print 'Skipping product'
                continue
        except KeyError:
            continue

        # Ensure the product is not a duplicate
        if is_duplicate(product['loc'], site['name']):
            print 'Duplicate product', product['loc']
            continue

        title = product['image:image']['image:title']
        has_tweeted, last_tweet = twitter.has_been_tweeted(title)
        if has_tweeted:
            print 'Not posting duplicated tweet for', product['loc']
            continue

        if tweet_count > 5:
            break

        tweet_date = parser.parse(last_tweet['created_at']).replace(tzinfo=None)
        x = (datetime.now() - tweet_date).total_seconds() / 60

        if x > 20:
            break

        # Check the products sold out status
        try:
            rp = requests.get('{}.json'.format(product['loc']), timeout=5)
            obj = json.loads(rp.content)
            have_stock = False

            try:
                for variant in obj['product']['variants']:
                    have_stock = have_stock or variant['inventory_quantity'] > 0

                if not have_stock:
                    continue
            except KeyError:
                pass

        except (requests.exceptions.HTTPError, ValueError):
            pass

        # Upload the product image
        try:
            media_id = twitter.upload_media(product['image:image']['image:loc'])
        except ValueError:
            media_id = None

        try:
            twitter.tweet('{} {}'.format(
                product['image:image']['image:title'],
                product['loc']
            ), media_id)
            tweet_count += 1

            dat_filename = 'locks/{}.dat'.format(site['name'])
            with open(dat_filename, 'a') as dat:
                dat.write('{}\n'.format(product['loc']))

        except UnicodeEncodeError:
            print 'Caught UnicodeEncodeError'

    # Update the lock
    with open(lock_filename, 'w') as lock:
        current_id = hashlib.sha224(first['loc']).hexdigest()
        lock.write('{} {}'.format(current_id, first['lastmod']))

