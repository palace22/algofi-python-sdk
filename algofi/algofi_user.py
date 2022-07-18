# IMPORTS

# global
from .lending.v2.lending_user import LendingUser
from .state_utils import *



# INTERFACE

class AlgofiUser:
    def __init__(self, algofi_client, address):
        self.algofi_client = algofi_client
        self.address = address
        
        self.load_state()
    
    def load_state(self):
        self.balances = get_balances(self.algofi_client.indexer, self.address)
        
        # lending
        self.lending = LendingUser(self.algofi_client.lending, self.address)
    
    def is_opted_in_to_asset(self, asset_id):
        return asset_id in self.balances