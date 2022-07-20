# IMPORTS

# external

# local
from .algofi_user import AlgofiUser
from .asset_config import ASSET_CONFIGS

# lending
from .lending.v2.lending_client import LendingClient


class AlgofiClient:
    def __init__(self, network, algod, indexer):
        self.network = network
        self.algod = algod
        self.indexer = indexer
        
        # assets
        self.assets = ASSET_CONFIGS[self.network]
        
        # lending
        self.lending = LendingClient(self)

    def get_user(self, address):
        return AlgofiUser(self, address)