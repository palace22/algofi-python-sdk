# IMPORTS

# global
from state_utils import *

# lending
from lending.lending_user import LendingUser

# INTERFACE

class AlgofiUser:
    def __init__(self, algofi_client, address):
        self.algofi_client = algofi_client
        self.address = address
        
        self.loadState()
    
    def loadState(self):
        self.balances = get_balances(self.algofi_client.indexer, self.address)
        self.states = get_local_states(self.algofi_client.indexer, self.address)
        
        # lending
        self.lending = LendingUser(self.algofi_client.lending, address)
    
    def isOptedInToAsset(self, asset_id):
        return asset_id in self.balances