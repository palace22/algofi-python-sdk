# IMPORTS

# global
from algosdk.v2client.indexer import IndexerClient

from algofipy.state_utils import get_global_state

# local

# INTERFACE


class Oracle:
    def __init__(self, indexer, app_id, price_field_name, scale_factor):
        """The python representation of an algofi lending market oracle

        :param indexer: Algorand indexer client
        :type indexer: :class:`IndexerClient`
        :param app_id: the app id of the oracle contract
        :type app_id: int
        :param price_field_name: the key of the price value in the smart contract global state
        :type price_field_name: int
        :param scale_factor: the number of decimals on the price value
        :type scale_factor: int
        """
        self.indexer = indexer
        self.app_id = app_id
        self.price_field_name = price_field_name
        self.scale_factor = scale_factor
        self.loadPrice()
    
    def loadPrice(self):
        """Populates the price field on the object

        :return: None
        """
        state = get_global_state(self.indexer, self.app_id)
        self.raw_price = state[self.price_field_name]