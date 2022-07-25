# IMPORTS

# global
from .lending.v2.lending_user import LendingUser
from .state_utils import *



# INTERFACE

class AlgofiUser:
    def __init__(self, algofi_client, address):
        """The python representation of an algofi user

        :param algofi_client: a client for the algofi protocol
        :type algofi_client: :class:`AlgofiClient`
        :param address: user wallet address
        :type address: str
        """
        self.algofi_client = algofi_client
        self.address = address
        
        self.load_state()
    
    def load_state(self):
        """Populates state on the :class:`AlgofiUser` object

        """
        self.balances = get_balances(self.algofi_client.indexer, self.address)
        
        # lending
        self.lending = LendingUser(self.algofi_client.lending, self.address)
    
    def is_opted_in_to_asset(self, asset_id):
        """Checks if user is opted is into a given asset

        :param asset_id: id of the asset
        :type asset_id: int
        :return: True if opted in, False otherwise
        :rtype: bool
        """
        return asset_id in self.balances