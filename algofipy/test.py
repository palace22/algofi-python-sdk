import sys
from algofipy.algofi_client import AlgofiClient
from algofipy.globals import Network
from algofipy.staking.v2.staking_user import StakingUser

sys.path.insert(0, "../../algofi-blockchain-utils")
from network_config import network_config
from offchain_utils import *
from onchain_utils import *

# getting algofi client
def get_client(algod_network, indexer_network):
    algod = algod_client(network_config, algod_network)
    indexer = indexer_client(network_config, indexer_network)
    algofi_client = AlgofiClient(Network.MAINNET, algod, indexer)
    return algofi_client

if __name__ == "__main__":
    algofi_client = get_client("ae_mainnet", "ae_mainnet")
    staking_user = StakingUser(algofi_client.staking, "S7JGWEKWJ2KEGMKI43FLV3QOF3VTCLMHSYNF3UNNVDW5WBYCE7II3LGUNE")
    staking_user.load_state()
    print(staking_user.user_staking_states)
    print(staking_user.opted_in_staking_contracts)