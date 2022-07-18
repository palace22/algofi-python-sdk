# IMPORTS

# global
from algofi.state_utils import get_global_state

# local

# INTERFACE


class Oracle:
    def __init__(self, indexer, app_id, price_field_name, scale_factor):
        self.indexer = indexer
        self.app_id = app_id
        self.price_field_name = price_field_name
        self.scale_factor = scale_factor
        self.loadPrice()
    
    def loadPrice(self):
        state = get_global_state(self.indexer, self.app_id)
        self.raw_price = state[self.price_field_name]