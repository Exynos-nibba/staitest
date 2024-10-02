from kivy.app import App
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
import os
import json
import time
from functools import partial

app = App.get_running_app()

def is_json(data):
    try:
        json.loads(data)
    except:
        return False
    return True

def write_oldata(fpath, data):
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(data)

def on_success(oldata, endpoint, req, bl):
    # Got new data, update the schedule
    ndata = None
    try:
        with open(req.file_path, 'r', encoding='utf-8') as f:
            ndata = f.read()
    except (IOError, ValueError) as e:
        print(f"Error reading {req.file_path}: {e}")
        return

    if ndata == oldata:
        return

    if not is_json(ndata):
        write_oldata(req.file_path, oldata)
        return

    # Check which endpoint got a response
    scr = {
        'schedule': 'screenschedule',
        'tracks': 'screentalks',
        'sponsors': 'screensponsor',
        'about': 'screenabout',
        'venue': 'screenvenue',
        'community': 'screencommunity',
        'event': 'screenschedule'
    }[endpoint]
    getattr(app, scr).on_enter(onsuccess=True)

def _check_data(req, oldata):
    ndata = None
    try:
        with open(req.file_path, 'r', encoding='utf-8') as f:
            ndata = f.read()
    except (IOError, ValueError) as e:
        print(f"Error reading {req.file_path}: {e}")
        return

    if ndata == oldata:
        return
    # Data is invalid in file; overwrite file with old data
    write_oldata(req.file_path, oldata)

def on_failure(oldata, endpoint, req, bl):
    _check_data(req, oldata)

def on_error(oldata, endpoint, req, bl):
    _check_data(req, oldata)

def fetch_remote_data(dt):
    '''Fetch remote data from the endpoint'''
    for args in fetch_remote_data._args:
        endpoint, filepath, oldata = args
        UrlRequest(
            # FIXME: initial URL should be abstracted out too.
            f'https://raw.githubusercontent.com/pythonindia/PyCon-Mobile-App/master/eventsapp/data/{endpoint}.json',
            file_path=filepath,
            on_success=partial(on_success, oldata, endpoint),
            on_error=partial(on_error, oldata, endpoint),
            on_failure=partial(on_failure, oldata, endpoint),
            timeout=15
        )
    fetch_remote_data._args = []

fetch_remote_data._args = []

trigger_fetch_remote_data = Clock.create_trigger(fetch_remote_data, 9)
'''Trigger fetching of data only once every 9 seconds'''

def get_data(endpoint, onsuccess=False):
    filepath = os.path.join(app.script_path, 'data', f'{endpoint}.json')

    # Use old data to check if anything in the data has been updated.
    oldata = None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            oldata = f.read()
    except (IOError, ValueError) as e:
        print(f"Error reading {filepath}: {e}")
        return {}

    if os.environ.get("PYCONF_OFFLINE_MODE", None) == '1':
        onsuccess = True
    if not onsuccess:
        fetch_remote_data._args.append([endpoint, filepath, oldata])
        trigger_fetch_remote_data()

    jsondata = json.loads(oldata)

    try:
        with open(filepath, 'r', encoding='utf-8') as fd:
            jsondata = json.load(fd)
    except (IOError, ValueError) as e:
        print(f"Error reading {filepath}: {e}")
        time.sleep(2)

    return jsondata
