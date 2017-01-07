#!/usr/bin/env python
import requests
import xmltodict
import hashlib
import json, os

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

    products = list(filter(lambda x: 'lastmod' in x and 'loc' in x, products))
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
            current_id = hashlib.sha224(first['loc']).hexdigest()
            lock.write('{} {}'.format(current_id, first['lastmod']))
        print 'Creating new lock file {}'.format(lock_filename)
        continue

    for product in products:
        id = hashlib.sha224(product['loc']).hexdigest()
        if id == previous[0]:
            break

        if twitter.has_been_tweeted(product['image:image']['image:title']):
            print 'Not posting duplicated tweet for', product['loc']
            continue

        media_id = twitter.upload_media(product['image:image']['image:loc'])
        twitter.tweet('[+] {} {}'.format(
            product['image:image']['image:title'],
            product['loc']
        ), media_id)

    # Update the lock
    with open(lock_filename, 'w') as lock:
        current_id = hashlib.sha224(first['loc']).hexdigest()
        lock.write('{} {}'.format(current_id, first['lastmod']))

