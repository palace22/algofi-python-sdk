# IMPORTS

# local
from base64 import b64encode, b64decode

from .globals import ALGO_ASSET_ID

# FUNCTIONS


def get_balances(indexer, address, block=None):
    """Get balances for a given user.

    :param indexer: algorand indexer client
    :type indexer: :class:`IndexerClient`
    :param address: user address
    :type address: str
    :param block: block at which to query balances
    :type block: int, optional
    :return: dict of asset id -> amount
    :rtype: dict
    """

    balances = {}
    account_info = indexer.account_info(address, round_num=block)["account"]
    balances[ALGO_ASSET_ID] = account_info["amount"]
    if "assets" in account_info:
        for asset_info in account_info["assets"]:
            balances[asset_info["asset-id"]] = asset_info["amount"]
    return balances


def get_state_int(state, key):
    """Get int value from state dict for given key.

    :param state: state dict of base64 key -> dict
    :type state: dict
    :param key: key of state dict
    :type key: str
    :return: int value for given key
    :rtype: int
    """

    if type(key) == str:
        key = b64encode(key.encode())
    return state.get(key.decode(), {"uint": 0})["uint"]


def get_state_bytes(state, key):
    """Get bytes value from state dict for given key.

    :param state: state dict of base64 key -> dict
    :type state: dict
    :param key: key of state dict
    :type key: str
    :return: bytes value for given key
    :rtype: bytes
    """

    if type(key) == str:
        key = b64encode(key.encode())
    return state.get(key.decode(), {"bytes": ""})["bytes"]


def format_state(state, decode_byte_values=True):
    """Format state dict by base64 decoding keys and, optionally, bytes values.

    :param state: state dict of base64 key -> dict
    :type state: dict
    :param decode_byte_values: whether to decode base64 bytes values to utf-8
    :type decode_byte_values: bool
    :return: formatted state dict
    :rtype: dict
    """

    formatted_state = {}
    for item in state:
        key = item["key"]
        value = item["value"]
        try:
            formatted_key = b64decode(key).decode("utf-8")
        except:
            formatted_key = b64decode(key)
        if value["type"] == 1:
            # byte string
            if decode_byte_values:
                try:
                    formatted_state[formatted_key] = b64decode(value["bytes"]).decode(
                        "utf-8"
                    )
                except:
                    formatted_state[formatted_key] = value["bytes"]
            else:
                formatted_state[formatted_key] = value["bytes"]
        else:
            # integer
            formatted_state[formatted_key] = value["uint"]
    return formatted_state


def format_prefix_state(state):
    """Format state dict including prefixes.

    :param state: state dict of base64 key -> dict
    :type state: dict
    :return: formatted state dict
    :rtype: dict
    """

    formatted_state = {}
    for key, value in state.items():
        try:
            index_of_underscore = key.index("_")
        except:
            index_of_underscore = -1
        # if the prefix actually exist
        if index_of_underscore > 0:
            prefix = key[0 : index_of_underscore + 1]
            raw_bytes = bytes(key[index_of_underscore + 1 :], "utf-8")
            formatted = int.from_bytes(raw_bytes, "big")
            formatted_state[prefix + str(formatted)] = value
        else:
            formatted_state[key] = value
    return formatted_state


def get_local_states(indexer, address, decode_byte_values=True, block=None):
    """Get local state of user for all opted in apps.

    :param indexer: algorand indexer
    :type indexer: :class:`IndexerClient`
    :param address: user address
    :type address: str
    :param decode_byte_values: whether to base64 decode bytes values
    :type decode_byte_values: bool
    :param block: block at which to query local state
    :type block: int, optional
    :return: formatted local state dict
    :rtype: dict
    """

    try:
        results = indexer.account_info(
            address, round_num=block, exclude="assets,created-apps,created-assets"
        ).get("account", {})
    except:
        raise Exception("Account does not exist.")

    result = {}
    if "apps-local-state" in results:
        for local_state in results["apps-local-state"]:
            result[local_state["id"]] = format_state(
                local_state.get("key-value", []), decode_byte_values=decode_byte_values
            )
    return result


def get_local_state_at_app(
    indexer, address, app_id, decode_byte_values=True, block=None
):
    """Get local state of user for given app.

    :param indexer: algorand indexer
    :type indexer: :class:`IndexerClient`
    :param address: user address
    :type address: str
    :param app_id: app id
    :type app_id: int
    :param decode_byte_values: whether to base64 decode bytes values
    :type decode_byte_values: bool
    :param block: block at which to query local state
    :type block: int, optional
    :return: formatted local state dict
    :rtype: dict
    """

    local_states = get_local_states(
        indexer, address, decode_byte_values=decode_byte_values, block=block
    )
    if app_id in local_states:
        return local_states[app_id]
    else:
        return None


def get_global_state(indexer, app_id, decode_byte_values=True, block=None):
    """Get global state of a given application.

    :param indexer: algorand indexer
    :type indexer: :class:`IndexerClient`
    :param app_id: app id
    :type app_id: int
    :param decode_byte_values: whether to base64 decode bytes values
    :type decode_byte_values: bool
    :param block: block at which to query global state
    :type block: int, optional
    :return: formatted global state dict
    :rtype: dict
    """

    try:
        application_info = indexer.applications(app_id, round_num=block).get(
            "application", {}
        )
    except:
        raise Exception("Application does not exist.")
    return format_state(
        application_info["params"]["global-state"],
        decode_byte_values=decode_byte_values,
    )


def get_global_state_field(
    indexer, app_id, field_name, decode_byte_values=True, block=None
):
    """Get global state field of a given application.

    :param indexer: algorand indexer
    :type indexer: :class:`IndexerClient`
    :param app_id: app id
    :type app_id: int
    :param field_name: name of the global state field
    :type field_name: str
    :param decode_byte_values: whether to base64 decode bytes values
    :type decode_byte_values: bool
    :param block: block at which to query global state
    :type block: int, optional
    :return: global state field
    :rtype: int / bytes
    """

    global_state = get_global_state(
        indexer, app_id, decode_byte_values=decode_byte_values, block=block
    )
    if field_name in global_state:
        return global_state[field_name]
    else:
        raise Exception("Field not found")


def get_accounts_opted_into_app(indexer, app_id, exclude=None):
    """Get list of accounts opted into a given app

    :param indexer: algorand indexer
    :type indexer: :class:`IndexerClient`
    :param app_id: app id
    :type app_id: int
    :param exclude: comma-delimited list of information to exclude from indexer call
    :type exclude: str, optional
    :return: formatted global state dict
    :rtype: dict
    """

    next_page = ""
    accounts = []
    while next_page != None:
        accounts_interim = indexer.accounts(
            next_page=next_page, limit=1000, application_id=app_id, exclude=exclude
        )
        accounts.extend(accounts_interim.get("accounts", []))
        next_page = accounts_interim.get("next-token", None)

    return accounts
