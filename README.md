## Project Setup
It is recommended to run the script inside of a virtual environment:

    pip install virtualenv

Then create the environment and install the `pip` dependencies as follows:

    virtualenv -p /usr/local/bin/python2 venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate

Then run the script calling the `python` in `bin/`:

    venv/bin/python2 vio.py

