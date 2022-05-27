# IMPORTS

# external
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

# local
from globals import Network
from algofi_user import AlgofiUser
from asset_config import ASSET_CONFIGS

# lending
from lending.lending_client import LendingClient

class AlgofiClient:
    def __init__(self, network, algod, indexer):
        self.network = network
        self.algod = algod
        self.indexer = indexer
        
        # assets
        self.assets = ASSET_CONFIGS[self.network]
        
        # lending
        self.lending = LendingClient(self)

    def getUser(self, address):
        return AlgofiUser(self, address)