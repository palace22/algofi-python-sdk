# IMPORTS

# local
from base64 import b64encode, b64decode

from .globals import ALGO_ASSET_ID

# FUNCTIONS

def get_balances(indexer, address):
    balances = {}
    account_info = indexer.account_info(address)['account']
    balances[ALGO_ASSET_ID] = account_info['amount']
    if 'assets' in account_info:
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

def format_state(state, decode_byte_values=True):
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
            if decode_byte_values:
                try:
                    formatted_state[formatted_key] = b64decode(value['bytes']).decode('utf-8')
                except:
                    formatted_state[formatted_key] = value['bytes']
            else:
                formatted_state[formatted_key] = value['bytes']
        else:
            # integer
            formatted_state[formatted_key] = value['uint']
    return formatted_state


def get_local_states(indexer, address, decode_byte_values=True):
    try:
        results = indexer.account_info(address).get("account", {})
    except:
        raise Exception("Account does not exist.")

    result = {}
    if 'apps-local-state' in results:
        for local_state in results['apps-local-state']:
            result[local_state['id']] = format_state(local_state.get('key-value', []), decode_byte_values=decode_byte_values)
    return result

def get_global_state(indexer, app_id, decode_byte_values=True):
    try:
        application_info = indexer.applications(app_id).get("application", {})
    except:
        raise Exception("Application does not exist.")
    return format_state(application_info["params"]["global-state"], decode_byte_values=decode_byte_values)

def format_prefix_state(state):
    formatted_state = {}
    for key, value in state.items():
        try:
            index_of_underscore = key.index("_")
        except:
            index_of_underscore = -1
        # if the prefix actually exist
        if index_of_underscore > 0:
            prefix = key[0: index_of_underscore + 1]
            raw_bytes = bytes(key[index_of_underscore + 1:], "utf-8")
            formatted = int.from_bytes(raw_bytes, "big")
            formatted_state[prefix + str(formatted)] = value
        else:
            formatted_state[key] = value
    return formatted_state