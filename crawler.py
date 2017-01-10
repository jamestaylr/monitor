#!/usr/bin/env python
import requests
import xmltodict
import hashlib
import json, os

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
        r = requests.get(site['url'])
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
    for product in products:
        id = hashlib.sha224(product['loc']).hexdigest()
        if id == previous[0]:
            break

        # Apply the keyword filter
        try:
            title = product['image:image']['image:title'].lower()
            if any(x in title for x in filter):
                print 'Skipping product'
                continue
        except KeyError:
            continue

        # Ensure the product is not a duplicate
        if is_duplicate(product['loc'], site['name']):
            print 'Duplicate product', product['loc']
            continue

        if twitter.has_been_tweeted(product['image:image']['image:title']):
            print 'Not posting duplicated tweet for', product['loc']
            continue

        media_id = twitter.upload_media(product['image:image']['image:loc'])
        try:
            dat_filename = 'locks/{}.dat'.format(site['name'])
            with open(dat_filename, 'a') as dat:
                dat.write('{}\n'.format(product['loc']))

            print 'Tweeting product', product['image:image']['image:title']
            twitter.tweet('{} {}'.format(
                product['image:image']['image:title'],
                product['loc']
            ), media_id)

        except UnicodeEncodeError:
            print 'Caught UnicodeEncodeError'

    # Update the lock
    with open(lock_filename, 'w') as lock:
        current_id = hashlib.sha224(first['loc']).hexdigest()
        lock.write('{} {}'.format(current_id, first['lastmod']))

