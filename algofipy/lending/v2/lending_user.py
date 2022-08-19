# IMPORTS

from base64 import b64decode

from algosdk.encoding import encode_address
# external
from algosdk.future.transaction import ApplicationNoOpTxn
# local
from .lending_config import MANAGER_STRINGS
from .user_market_state import UserMarketState
# INTERFACE
from ...globals import FIXED_3_SCALE_FACTOR #,PERMISSIONLESS_SENDER_LOGIC_SIG
from ...state_utils import get_local_state_at_app, get_local_states
from ...transaction_utils import TransactionGroup
from ...utils import int_to_bytes, bytes_to_int


class LendingUser:
    def __init__(self, lending_client, address):
        """An object that encapsulates user state on the lending protocol
        and creates transactions representing user actions

        :param lending_client: a client for interacting with the algofi lending protocol
        :type lending_client: :class:`LendingClient`
        :param address: an address of the user wallet
        :type address: str
        """

        self.lending_client = lending_client
        self.address = address
        
        self.load_state()
    
    def load_state(self, block=None):
        """Populates user state from the blockchain on the object

        :param block: block at which to query the user local state
        :type block: int, optional
        """

        manager_state = get_local_state_at_app(self.lending_client.indexer, self.address, self.lending_client.manager.app_id)

        # reset state
        self.opted_in_market_count = 0
        self.opted_in_markets = []
        self.user_market_states = {}
        self.net_collateral = 0
        self.net_scaled_collateral = 0
        self.net_borrow = 0
        self.net_scaled_borrow = 0
        dollar_totaled_supply_apr = 0
        dollar_totaled_borrow_apr = 0
        self.net_supply_apr = 0
        self.net_borrow_apr = 0

        if manager_state:
            self.opted_in_to_manager = True
            self.storage_address = encode_address(b64decode(manager_state[MANAGER_STRINGS.storage_account]))

            indexer = self.lending_client.historical_indexer if block else self.lending_client.indexer
            storage_states = get_local_states(indexer, self.storage_address, decode_byte_values=False, block=block)

            self.opted_in_market_count = storage_states[self.lending_client.manager.app_id].get(MANAGER_STRINGS.opted_in_market_count, 0)
            for page_idx in range((self.opted_in_market_count // 3) + 1):
                market_page = b64decode(storage_states[self.lending_client.manager.app_id].get(MANAGER_STRINGS.opted_in_markets_page_prefix + int_to_bytes(page_idx).decode().strip(), ''))
                for market_offset in range(int(len(market_page)//8)):
                    self.opted_in_markets.append(bytes_to_int(market_page[market_offset*8:(market_offset+1)*8]))
        
            for market_app_id in self.opted_in_markets:
                # cache local state
                if market_app_id in self.lending_client.markets:
                    market = self.lending_client.markets[market_app_id]
                    market.load_state(block=block)

                    self.user_market_states[market_app_id] = UserMarketState(market, storage_states[market_app_id])
                    
                    # total net values
                    user_market_state = self.user_market_states[market_app_id]
                    self.net_collateral += user_market_state.b_asset_collateral_underlying.usd
                    self.net_scaled_collateral += user_market_state.b_asset_collateral_underlying.usd * market.collateral_factor / FIXED_3_SCALE_FACTOR
                    self.net_borrow += user_market_state.borrowed_underlying.usd
                    self.net_scaled_borrow += user_market_state.borrowed_underlying.usd * market.borrow_factor / FIXED_3_SCALE_FACTOR
                    dollar_totaled_supply_apr += user_market_state.b_asset_collateral_underlying.usd * market.supply_apr
                    dollar_totaled_borrow_apr += user_market_state.borrowed_underlying.usd * market.borrow_apr
            if self.net_collateral > 0:
                self.net_supply_apr = dollar_totaled_supply_apr / self.net_collateral
            if self.net_borrow > 0:
                self.net_borrow_apr = dollar_totaled_borrow_apr / self.net_borrow
        else:
            self.opted_in_to_manager = False
    
    def get_market_page_offset(self, market_app_id):
        """Helper function that returns the location of the by-market state for the user
        
        :param market_app_id: the market app id for which the location is being calculated
        :type market_app_id: int
        :return: a tuple of page, offset ints
        :rtype: tuple
        """

        for i in range(len(self.opted_in_markets)):
            if self.opted_in_markets[i] == market_app_id:
                return int(i / 3), i % 3
        return 0, 0
    
    def get_preamble_txns(self, params, target_market_app_id, sender_address=''):
        """Helper function that constructs a group representing the utility transactions
        that should precede some user calls to the algofi protocol markets

        :param params: suggested params for the algod client
        :type params: dict
        :param target_market_app_id: the market contract for this group
        :type target_market_app_id: int
        :param sender_address: the address of the sender for the preamble transactions. This is helpful for liquidators, who are sending preamble transactions from their own accounts, targeting some user's storage account
        :return: preamble transaction group
        :rtype: :class:`TransactionGroup`
        """

        page_count = int((self.opted_in_market_count - 1) / 3) + 1
        
        txns = []

        if not sender_address:
            sender_address = self.address
        
        for page in range(page_count):
            app_args = [bytes(MANAGER_STRINGS.calculate_user_position, "utf-8"), int_to_bytes(page), int_to_bytes(target_market_app_id)]
            accounts = [self.storage_address]
            foreign_apps = self.opted_in_markets[page * 3 : (page + 1) * 3] + [self.lending_client.markets[market_app_id].oracle.app_id for market_app_id in self.opted_in_markets[page * 3 : (page + 1) * 3]]
            txns.append(ApplicationNoOpTxn(sender_address, params, self.lending_client.manager.app_id, app_args, accounts=accounts, foreign_apps=foreign_apps))
        
        return TransactionGroup(txns)
