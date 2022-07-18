# IMPORTS

# local
from base64 import b64encode, b64decode

from .globals import ALGO_ASSET_ID

# FUNCTIONS

def get_balances(indexer, address):
    balances = {}
    account_info = indexer.account_info(address)['account']
    balances[ALGO_ASSET_ID] = account_info['amount']
    for asset_info in account_info['assets']:
        balances[asset_info['asset-id']] = asset_info['amount']
    return balances
    
def get_state_int(state, key):
    if type(key) == str:
        key = b64encode(key.encode())
    return state.get(key.decode(), {'uint': 0})['uint']

def get_state_bytes(state, key):
    if type(key) == str:
        key = b64encode(key.encode())
    return state.get(key.decode(), {'bytes': ''})['bytes']

def format_state(state):
    formatted_state = {}
    for item in state:
        key = item['key']
        value = item['value']
        try:
            formatted_key = b64decode(key).decode('utf-8')
        except:
            formatted_key = b64decode(key)
        if value['type'] == 1:
            # byte string
            try:
                formatted_state[formatted_key] = b64decode(value['bytes']).decode('utf-8')
            except:
                formatted_state[formatted_key] = value['bytes']
        else:
            # integer
            formatted_state[formatted_key] = value['uint']
    return formatted_state


def get_local_states(indexer, address):
    try:
        results = indexer.account_info(address).get("account", {})
    except:
        raise Exception("Account does not exist.")

    result = {}
    for local_state in results['apps-local-state']:
        result[local_state['app-id']] = format_state(local_state.get('key-value', []))
    return result

def get_global_state(indexer, app_id):
    try:
        application_info = indexer.applications(app_id).get("application", {})
    except:
        raise Exception("Application does not exist.")
    return format_state(application_info["params"]["global-state"])