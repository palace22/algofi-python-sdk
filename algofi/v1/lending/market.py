# IMPORTS

# global
from ..globals import FIXED_3_SCALE_FACTOR, FIXED_6_SCALE_FACTOR, PERMISSIONLESS_SENDER_LOGIC_SIG
from ..state_utils import *
from ..transaction_utils import *
from ..asset_amount import AssetAmount

# local
from lending_config import MARKET_STRINGS
from market_config import MarketConfig
from oracle import Oracle

# CONSTANTS

NEEDS_USER_POSITION = True
DOESNT_NEED_USER_POSITION = False

# INTERFACE

class Market:
    def __init__(self, lending_client, market_config):
        self.lending_client = lending_client
        self.algod = self.lending_client.algod
        self.indexer = self.lending_client.indexer
        self.manger_app_id = lending_client.manager.app_id
        
        self.app_id = market_config.app_id
        self.underlying_asset_id = market_config.underlying_asset_id
        self.b_asset_id = market_config.b_asset_id
        self.market_type = market_config.market_type
        
        self.loadState()
        
    def loadState(self):
        state = get_global_state(self.indexer, self.app_id)
        
        # parameters
        self.borrow_factor = state.get(MARKET_STRINGS.borrow_factor, 0)
        self.collateral_factor = state.get(MARKET_STRINGS.collateral_factor, 0)
        self.flash_loan_fee = state.get(MARKET_STRINGS.flash_loan_fee, 0)
        self.flash_loan_protocol_fee = state.get(MARKET_STRINGS.flash_loan_protocol_fee, 0)
        self.max_flash_loan_ratio = state.get(MARKET_STRINGS.max_flash_loan_ratio, 0)
        self.liquidation_incentive = state.get(MARKET_STRINGS.liquidation_incentive, 0)
        self.liquidation_fee = state.get(MARKET_STRINGS.liquidation_fee, 0)
        self.reserve_factor = state.get(MARKET_STRINGS.reserve_factor, 0)
        self.underlying_supply_cap = state.get(MARKET_STRINGS.underlying_supply_cap, 0)
        self.underlying_borrow_cap = state.get(MARKET_STRINGS.underlying_borrow_cap, 0)
    
        # interest rate model
        self.base_interest_rate = state.get(MARKET_STRINGS.base_interest_rate, 0)
        self.base_interest_slope = state.get(MARKET_STRINGS.base_interest_slope, 0)
        self.exponential_interest_amplification_factor = state.get(MARKET_STRINGS.exponential_interest_amplification_factor, 0)
        self.target_utilization_ratio = state.get(MARKET_STRINGS.target_utilization_ratio, 0)
    
        # oracle
        self.oracle = Oracle(self.algod,
                             state.get(MARKET_STRINGS.oracle_app_id, 0),
                             Base64Encoder.decode(state.get(MARKET_STRINGS.oracle_price_field_name, 0)),
                             state.get(MARKET_STRINGS.oracle_price_scale_factor, 0))
        self.oracle.loadPrice()
    
        # balance
        self.underlying_cash = state.get(MARKET_STRINGS.underlying_cash, 0)
        self.underlying_borrowed = state.get(MARKET_STRINGS.underlying_borrowed, 0)
        self.underlying_reserves = state.get(MARKET_STRINGS.underlying_reserves, 0)
        self.borrow_share_circulation = state.get(MARKET_STRINGS.borrow_share_circulation, 0)
        self.b_asset_circulation = state.get(MARKET_STRINGS.b_asset_circulation, 0)
        self.active_b_asset_collateral = state.get(MARKET_STRINGS.active_b_asset_collateral, 0)
        self.underlying_protocol_reserve = state.get(MARKET_STRINGS.underlying_protocol_reserve, 0)
    
        # interest
        self.latest_time = state.get(MARKET_STRINGS.latest_time, 0)
        self.borrow_index= state.get(MARKET_STRINGS.borrow_index, 0)
        self.implied_borrow_index = state.get(MARKET_STRINGS.implied_borrow_index, 0)
        
        # calculated values
        self.total_supplied = AssetAmount(
          self.getUnderlyingSupplied() / (10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals),
          self.underlyingToUSD(self.getUnderlyingSupplied())
        )
        
        self.total_borrowed = AssetAmount(
          self.underlying_borrowed / 10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals,
          self.underlyingToUSD(self.underlying_borrowed)
        )
        
        self.supply_apr, self.borrow_apr = self.getAPRs(self.total_supplied.underlying, self.total_borrowed.underlying)
    
    # GETTERS
    
    def getUnderlyingSupplied(self):
        if this.market_type == MarketType.STBL:
            return this.underlying_cash
        else:
            return this.underlying_borrowed + this.underlying_cash - this.underlying_reserves
  
    def getAPRs(self, total_supplied, total_borrowed):
        borrow_utilization = 0 if total_supplied == 0 else total_borrowed / total_supplied
        borrow_apr = self.base_interest_rate / FIXED_6_SCALE_FACTOR
        borrow_apr += borrow_utilization * self.base_interest_slope / FIXED_6_SCALE_FACTOR
        if borrow_utilization > (self.target_utilization_ratio / FIXED_6_SCALE_FACTOR):
            borrow_apr += self.exponential_interest_amplification_factor * ((borrow_utilization - self.target_utilization_ratio / FIXED_6_SCALE_FACTOR)**2)
        supply_apr = borrow_apr * borrow_utilization * (1 - self.reserve_factor / FIXED_6_SCALE_FACTOR)
        return supply_apr, borrow_apr
    
    # CONVERSIONS
    
    def underlyingToUSD(self, amount):
        return (amount * self.oracle.raw_price) / (self.oracle.scale_factor * FIXED_3_SCALE_FACTOR)
    
    def bAssetToAssetAmount(self, amount):
        if amount == 0:
            return AssetAmount(0, 0)
        raw_underlying_amount = amount * self.getUnderlyingSupplied() / self.b_asset_circulation
        underlying_amount = raw_underlying_amount / 10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals
        usd_amount = self.underlyingToUSD(raw_underlying_amount)
        return AssetAmount(underlying_amount, usd_amount)
    
    def borrowSharesToAssetAmount(self, amount):
        if amount == 0:
            return AssetAmount(0, 0)
        raw_underlying_amount = amount * self.underlying_borrowed / self.borrow_share_circulation
        underlying_amount = raw_underlying_amount / 10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals
        usd_amount = self.underlyingToUSD(raw_underlying_amount)
        return AssetAmount(underlying_amount, usd_amount)
    
    def underlyingToBAssetAmount(self, amount):
        return amount * self.b_asset_circulation / self.getUnderlyingSupplied()
    
    # TRANSACTION BUILDERS
