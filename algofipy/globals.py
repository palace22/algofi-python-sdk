# IMPORTS

# external
from algosdk.future.transaction import LogicSig
from algosdk.future.transaction import LogicSigAccount

# CONSTANTS

FIXED_3_SCALE_FACTOR = 1000
FIXED_6_SCALE_FACTOR = 1000000
FIXED_9_SCALE_FACTOR = 1000000000
FIXED_12_SCALE_FACTOR = 1000000000000
FIXED_15_SCALE_FACTOR = 1000000000000000
FIXED_18_SCALE_FACTOR = 1000000000000000000

ALGO_ASSET_ID = 1

# ENUMS

class Network:
    """Enum specifying the network
    """

    MAINNET = 0
    MAINNET_CLONE = 1
    MAINNET_CLONE2 = 2
    TESTNET = 3

# LOGIC SIG
PERMISSIONLESS_SENDER_LOGIC_SIG = LogicSigAccount([6, 49, 16, 129, 6, 18, 68, 49, 25, 129, 0, 18, 68, 49, 9, 50, 3, 18, 68, 49, 32, 50, 3, 18, 68, 129, 1, 67])

# ANALYTICS ENDPOINT
MAINNET_ANALYTICS_ENDPOINT = "https://api.algofi.org"
TESTNET_ANALYTICS_ENDPOINT = "https://api-dev.algofi.org"

def get_analytics_endpoint(network):
    """Get Algofi analytics endpoint for given network

    :param network: algofi network
    :type network: :class:`Network`
    :return: algofi analytics url
    :rtype: str
    """

    if network == Network.MAINNET:
        return MAINNET_ANALYTICS_ENDPOINT
    else:
        return TESTNET_ANALYTICS_ENDPOINT