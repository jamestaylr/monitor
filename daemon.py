#!/usr/bin/env python
from datetime import datetime
import time, os
import subprocess

# Read the configuration
import ConfigParser
config = ConfigParser.ConfigParser()
config.read('config.ini')

# Setup execution
null = open(os.devnull, 'w')
offset = config.getint('daemon', 'execution_offset')

while True:
    # Conduct execution
    subprocess.call(['venv/bin/python2', 'monitor.py'],
            bufsize=4096, stdout=null, stderr=null)

    # Calculate the dyanmic wait time
    t = datetime.utcnow()
    sleeptime = offset - (t.second + t.microsecond / 1000000.0)
    if sleeptime < 0:
        sleeptime = 60 - abs(sleeptime)

    print 'Sleeping for', sleeptime, 'seconds'
    time.sleep(sleeptime)
