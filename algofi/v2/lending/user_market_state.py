# IMPORTS

# local
from lending_config import MANAGER_STRINGS, MARKET_STRINGS

# INTERFACE

class UserMarketState:
    def __init__(self, market, state):
        self.b_asset_collateral = state.get(MARKET_STRINGS.user_active_b_asset_collateral, 0)
        self.borrow_shares = state.get(MARKET_STRINGS.user_borrow_shares, 0)
        self.supplied_amount = market.b_asset_to_asset_amount(self.b_asset_collateral)
        self.borrowed_amount = market.borrow_shares_to_asset_amount(self.borrow_shares)