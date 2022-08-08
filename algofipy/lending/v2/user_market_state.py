# IMPORTS
from base64 import b64decode

from .lending_config import MARKET_STRINGS
# INTERFACE
from ...utils import int_to_bytes, bytes_to_int


class UserMarketState:
    def __init__(self, market, state):
        """Local state of the user with a given market

        :param market: Algofi market
        :type market: :class:`Market`
        :param state: raw user local state for given market
        :type state: dict
        """

        self.b_asset_collateral = state.get(MARKET_STRINGS.user_active_b_asset_collateral, 0)
        self.b_asset_collateral_underlying = market.b_asset_to_asset_amount(self.b_asset_collateral)
        self.borrow_shares = state.get(MARKET_STRINGS.user_borrow_shares, 0)
        self.borrowed_underlying = market.borrow_shares_to_asset_amount(self.borrow_shares)
        self.rewards_states = []
        for i in range(market.max_rewards_program_index + 1):
            self.rewards_states.append(UserRewardsState(state, i))

class UserRewardsState:
    def __init__(self, state, program_index):
        """Local state of the user for a single rewards program on a given market

        :param state: raw user local state for given market
        :type state: dict
        :param program_index: index of the rewards program on the market
        :type program_index: int
        """

        program_index_bytestr = int_to_bytes(program_index).decode()
        program_index_key = MARKET_STRINGS.user_rewards_program_number_prefix + program_index_bytestr
        latest_rewards_index_key = MARKET_STRINGS.user_latest_rewards_index_prefix + program_index_bytestr
        unclaimed_rewards_key = MARKET_STRINGS.user_unclaimed_rewards_prefix + program_index_bytestr

        self.rewards_program_number = state.get(program_index_key, 0)
        self.latest_rewards_index = bytes_to_int(b64decode(state.get(latest_rewards_index_key, 0)))
        self.unclaimed_rewards = state.get(unclaimed_rewards_key, 0)