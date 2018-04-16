This project contains a collection of scripts which, when called, will access the publicly accessible RESTful `/products.json` endpoint of various Shopify websites maintained in `data.json`.

The `monitor.py` script is intended to be run at high frequencies, sleeping for 1 minute between calls.

## Project Setup
It is recommended to run the script inside of a virtual environment:

    sudo pip install virtualenv

Then create the environment and install the `pip` dependencies as follows:

    virtualenv -p $(which python) venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate

Then run the script calling the `python` in `bin/`:

    venv/bin/python2 monitor.py

