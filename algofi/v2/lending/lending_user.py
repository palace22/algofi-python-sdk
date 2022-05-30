# IMPORTS

# external
from algosdk.future.transactions import *
from algosdk.encoding import encode_address
from base64 import b64decode

# global
from ..globals import FIXED_3_SCALE_FACTOR, FIXED_6_SCALE_FACTOR, PERMISSIONLESS_SENDER_LOGIC_SIG
from ..state_utils import *
from ..transaction_utils import *
from ..asset_amount import AssetAmount

# local
from .lending_config import MANAGER_STRINGS, MARKET_STRINGS
from .market_config import MarketConfig
from .user_market_state import UserMarketState
from .oracle import Oracle

# INTERFACE

class LendingUser:
    def __init__(self, lending_client, address):
        self.lending_client = lending_client
        self.address = address
        
        self.load_state()
    
    def load_state(self):
        states = get_local_states(self.lending_client.algofi_client.indexer, self.address)

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

        if (self.lending_client.manager_app_id in states):
            self.opted_in_to_manager = True
            self.storage_address = encode_address(b64decode(states[self.lending_client.manager_app_id][MANAGER_STRINGS.storage_account]))
            
            storage_states = get_local_states(self.lending_client.algofi_client.indexer, self.storage_address)
        
            self.opted_in_market_count = storage_states[self.lending_client.manager_app_id].get(MANAGER_STRINGS.opted_in_market_count, 0)
            for page_idx in range((self.opted_in_market_count / 3) + 1):
                market_page = storage_account_local_states[self.lending_client.manager_app_id].get(MANAGER_STRINGS.opted_in_markets_page_prefix + int_to_bytes(page_idx).decode().strip(), b'')
                for market_offset in range(int(len(market_page)/8)):
                    self.opted_in_markets.append(bytes_to_int(market_page[market_offset*8:(market_offset+1)*8]))
        
            for market_app_id in self.opted_in_markets:
                # cache local state
                market = self.lending_client.markets[market_app_id]
                self.user_market_states[market_app_id] = UserMarketState(market, storage_states[market_app_id])
                
                # total net values
                user_market_state = self.user_market_states[market_app_id]
                self.net_collateral += user_market_state.supplied_amount.usd
                self.net_scaled_collateral += user_market_state.supplied_amount.usd * market.collateral_factor / FIXED_3_SCALE_FACTOR
                self.net_borrow += user_market_state.borrowed_amount.usd
                self.net_scaled_borrow += user_market_state.borrowed_amount.usd * market.borrow_factor / FIXED_3_SCALE_FACTOR
                dollar_totaled_supply_apr += user_market_state.supplied_amount.usd * market.supply_apr
                dollar_totaled_borrow_apr += user_market_state.borrowed_amount.usd * market.borrow_apr
            if self.net_collateral > 0:
                self.net_supply_apr = dollar_totaled_supply_apr / self.net_collateral
            if self.net_borrow > 0:
                self.net_borrow_apr = dollar_totaled_borrow_apr / self.net_borrow

        else:
            self.opted_in_to_manager = False
    
    def get_market_page_offset(self, market_app_id):
        for i in range(len(self.opted_in_markets)):
            if self.opted_in_markets[i] == market_app_id:
                return int(i / 3), i % 3
        return 0, 0
    
    def get_preamble_txns(self, params, target_market_app_id):
        page_count = int((self.opted_in_market_count - 1) / 3) + 1
        
        txns = []
        
        for page in range(page_count):
            app_args = [bytes(MANAGER_STRINGS.calculate_user_position, "utf-8"), int_to_bytes(page), int_to_bytes(target_market_app_id)]
            accounts = [self.storage_address]
            foreign_apps = self.opted_in_markets[page * 3 : (page + 1) * 3] + [self.lending_client.markets[market_app_id].oracle.app_id for market_app_id in self.opted_in_markets[page * 3 : (page + 1) * 3]]
            txns.append(ApplicationNoOpTxn(PERMISSIONLESS_SENDER_LOGIC_SIG.address(), params, market_state.app_id, app_args, accounts=accounts, foreign_apps=foreign_apps))
        
        return TransactionGroup(txns)