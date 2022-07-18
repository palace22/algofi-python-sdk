# IMPORTS
from algosdk.future.transaction import ApplicationOptInTxn
from algosdk.logic import get_application_address
from nacl.encoding import Base64Encoder

from .lending_config import MARKET_STRINGS, MarketType
from .oracle import Oracle


# INTERFACE
from ...asset_amount import AssetAmount
from ...globals import FIXED_3_SCALE_FACTOR, FIXED_6_SCALE_FACTOR
from ...state_utils import get_global_state
from ...transaction_utils import TransactionGroup, get_default_params, get_payment_txn
from ...utils import int_to_bytes


class Market:
    def __init__(self, lending_client, market_config):
        """
        :param lending_client:
        :type lending_client: :class: `LendingMarket`
        :param market_config:
        """
        self.lending_client = lending_client
        self.algod = self.lending_client.algod
        self.indexer = self.lending_client.indexer
        self.manger_app_id = lending_client.manager.app_id
        
        self.app_id = market_config.app_id
        self.address = get_application_address(self.app_id)
        self.underlying_asset_id = market_config.underlying_asset_id
        self.b_asset_id = market_config.b_asset_id
        self.market_type = market_config.market_type
        
        self.load_state()
        
    def load_state(self):
        """
        Loads market state from the blockchain
        :rtype: None
        """
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
          self.get_underlying_supplied() / (10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals),
          self.underlying_to_usd(self.get_underlying_supplied())
        )
        
        self.total_borrowed = AssetAmount(
          self.underlying_borrowed / 10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals,
          self.underlying_to_usd(self.underlying_borrowed)
        )
        
        self.supply_apr, self.borrow_apr = self.get_aprs(self.total_supplied.underlying, self.total_borrowed.underlying)
    
    # GETTERS
    
    def get_underlying_supplied(self):
        if self.market_type == MarketType.STBL:
            return self.underlying_cash
        else:
            return self.underlying_borrowed + self.underlying_cash - self.underlying_reserves
  
    def get_aprs(self, total_supplied, total_borrowed):
        borrow_utilization = 0 if total_supplied == 0 else total_borrowed / total_supplied
        borrow_apr = self.base_interest_rate / FIXED_6_SCALE_FACTOR
        borrow_apr += borrow_utilization * self.base_interest_slope / FIXED_6_SCALE_FACTOR
        if borrow_utilization > (self.target_utilization_ratio / FIXED_6_SCALE_FACTOR):
            borrow_apr += self.exponential_interest_amplification_factor * ((borrow_utilization - self.target_utilization_ratio / FIXED_6_SCALE_FACTOR)**2)
        supply_apr = borrow_apr * borrow_utilization * (1 - self.reserve_factor / FIXED_6_SCALE_FACTOR)
        return supply_apr, borrow_apr
    
    # CONVERSIONS
    
    def underlying_to_usd(self, amount):
        return (amount * self.oracle.raw_price) / (self.oracle.scale_factor * FIXED_3_SCALE_FACTOR)
    
    def b_asset_to_asset_amount(self, amount):
        if amount == 0:
            return AssetAmount(0, 0)
        raw_underlying_amount = amount * self.get_underlying_supplied() / self.b_asset_circulation
        underlying_amount = raw_underlying_amount / 10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals
        usd_amount = self.underlying_to_usd(raw_underlying_amount)
        return AssetAmount(underlying_amount, usd_amount)
    
    def borrow_shares_to_asset_amount(self, amount):
        if amount == 0:
            return AssetAmount(0, 0)
        raw_underlying_amount = amount * self.underlying_borrowed / self.borrow_share_circulation
        underlying_amount = raw_underlying_amount / 10**self.lending_client.algofi_client.assets[self.underlying_asset_id].decimals
        usd_amount = self.underlying_to_usd(raw_underlying_amount)
        return AssetAmount(underlying_amount, usd_amount)
    
    def underlying_to_b_asset(self, amount):
        return amount * self.b_asset_circulation / self.get_underlying_supplied()
    
    # TRANSACTION BUILDERS

    def get_mint_txns(self, user, underlying_amount):
        """Returns a :class:`TransactionGroup` object representing a mint bank asset group
        transaction against the algofi protocol. Sender mints bank asset by sending underlying asset
        to the account address of the market application which sends back the bank asset.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param underlying_amount: amount of underlying asset to use in minting
        :type underlying_amount: int
        :return: :class:`TransactionGroup` object representing a mint group transaction
        :rtype: :class:`TransactionGroup`
        """
        assert self.market_type != MarketType.VAULT
        
        params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(user.address, params, self.address, underlying_amount, self.underlying_asset_id)
        
        # application call
        params.fee = 2000
        app_args1 = [bytes(MARKET_STRINGS.mint_b_asset)]
        foreign_apps1 = [self.manger_app_id]
        foreign_assets1 = [self.b_asset_id]
        txn1 = ApplicationOptInTxn(user.address, params, self.app_id, app_args1, foreign_apps=foreign_apps1, foreign_assets=foreign_assets1)
        
        return TransactionGroup([txn0, txn1])

    def get_add_underlying_collateral_txns(self, user, underlying_amount):
        """Returns a :class:`TransactionGroup` object representing an add collateral group
        transaction against the algofi protocol. Sender adds underlying asset amount to collateral by sending
        it to the account address of the market application that updates user active collateral.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param underlying_amount: amount of underlying asset to add to collateral
        :type underlying_amount: int
        :return: :class:`TransactionGroup` object representing an add collateral group transaction
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        # payment
        receiver = self.address if self.market_type != MarketType.VAULT else user.storage_address
        txn0 = get_payment_txn(user.address, params, receiver, underlying_amount, self.underlying_asset_id)
        
        # application call
        app_args1 = [bytes(MARKET_STRINGS.add_underlying_collateral)]
        accounts1 = [user.storage_address]
        foreign_apps1 = [self.manger_app_id]
        txn1 = ApplicationOptInTxn(user.address, params, self.app_id, app_args1, accounts=accounts1, foreign_apps=foreign_apps1)
        
        return TransactionGroup([txn0, txn1])
        
    def get_add_b_asset_collateral_txns(self, user, b_asset_amount):
        """Returns a :class:`TransactionGroup` object representing an add collateral group
        transaction against the algofi protocol. Sender adds bank asset amount to collateral by sending
        them to the account address of the market application that generates the bank assets.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param b_asset_amount: amount of bank asset to add to collateral
        :type b_asset_amount: int
        :return: :class:`TransactionGroup` object representing an add collateral group transaction
        :rtype: :class:`TransactionGroup`
        """

        assert self.market_type != MarketType.VAULT
        
        params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(user.address, params, self.address, b_asset_amount, self.b_asset_id)
        
        # application call
        app_args1 = [bytes(MARKET_STRINGS.add_b_asset_collateral)]
        accounts1 = [user.storage_address]
        foreign_apps1 = [self.manger_app_id]
        txn1 = ApplicationOptInTxn(user.address, params, self.app_id, app_args1, accounts=accounts1, foreign_apps=foreign_apps1)
        
        return TransactionGroup([txn0, txn1])
        
    def get_remove_underlying_collateral_txns(self, user, underlying_amount):
        """Returns a :class:`TransactionGroup` object representing a remove collateral group
        transaction against the algofi protocol. Sender reclaims underlying collateral asset by reducing their active
        collateral.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param underlying_amount: amount of underlying asset to remove
        :type underlying_amount: int
        :return: :class:`TransactionGroup` object representing a remove collateral group transaction
        :rtype: :class:`TransactionGroup`
        """
        params = get_default_params(self.algod)

        preamble_txns = user.get_preamble_txns(params, self.app_id)

        # application call
        params.fee = 2000 + 1000 * preamble_txns.length() if self.market_type != MarketType.VAULT else 3000 + 1000 * preamble_txns.length()
        app_args0 = [bytes(MARKET_STRINGS.remove_underlying_collateral), int_to_bytes(underlying_amount)]
        accounts0 = [user.storage_address]
        foreign_apps0 = [self.manger_app_id]
        foreign_assets0 = [self.underlying_asset_id]
        txn0 = ApplicationOptInTxn(user.address, params, self.app_id, app_args0, accounts=accounts0, foreign_apps=foreign_apps0, foreign_assets=foreign_assets0)
        
        return preamble_txns + TransactionGroup([txn0])
        
    def get_remove_b_asset_collateral_txns(self, user, b_asset_amount):
        """Returns a :class:`TransactionGroup` object representing a remove collateral group
        transaction against the algofi protocol. Sender reclaims collateral bank asset by reducing their active
        collateral.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param b_asset_amount: amount of underlying asset to remove
        :type b_asset_amount: int
        :return: :class:`TransactionGroup` object representing a remove collateral group transaction
        :rtype: :class:`TransactionGroup`
        """
        assert self.market_type != MarketType.VAULT
        
        params = get_default_params(self.algod)

        preamble_txns = user.get_preamble_txns(self.app_id)

        # application call
        params.fee = 2000 + 1000 * preamble_txns.length()
        app_args0 = [bytes(MARKET_STRINGS.remove_b_asset_collateral), int_to_bytes(b_asset_amount)]
        accounts0 = [user.storage_address]
        foreign_apps0 = [self.manger_app_id]
        foreign_assets0 = [self.b_asset_id]
        txn0 = ApplicationOptInTxn(user.address, params, self.app_id, app_args0, accounts=accounts0, foreign_apps=foreign_apps0, foreign_assets=foreign_assets0)
        
        return preamble_txns + TransactionGroup([txn0])
    
    def get_burn_txns(self, user, b_asset_amount):
        """Returns a :class:`TransactionGroup` object representing a burn group
        transaction against the algofi protocol. Sender reclaims underlying collateral asset by burning bank asset.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param b_asset_amount: amount of underlying asset to remove
        :type b_asset_amount: int
        :return: :class:`TransactionGroup` object representing a burn group transaction
        :rtype: :class:`TransactionGroup`
        """
        assert self.market_type != MarketType.VAULT
        
        params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(user.address, params, self.address, b_asset_amount, self.b_asset_id)
        
        # application call
        app_args1 = [bytes(MARKET_STRINGS.burn_b_asset)]
        foreign_apps1 = [self.manger_app_id]
        foreign_assets1 = [self.underlying_asset_id]
        txn1 = ApplicationOptInTxn(user.address, params, self.app_id, app_args1, foreign_apps=foreign_apps1, foreign_assets=foreign_assets1)
        
        return TransactionGroup([txn0, txn1])

    def get_borrow_txns(self, user, underlying_amount):
        """Returns a :class:`TransactionGroup` object representing a borrow group
        transaction against the algofi protocol. Sender borrows underlying asset against their
        collateral in the protocol.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param underlying_amount: amount to borrow
        :type underlying_amount: int
        :return: :class:`TransactionGroup` object representing a borrow group transaction
        :rtype: :class:`TransactionGroup`
        """
        assert self.market_type != MarketType.VAULT
        
        params = get_default_params(self.algod)

        preamble_txns = user.get_preamble_txns(params, self.app_id)

        # application call
        params.fee = 2000 + 1000 * preamble_txns.length()
        app_args0 = [bytes(MARKET_STRINGS.borrow), int_to_bytes(underlying_amount)]
        accounts0 = [user.storage_address]
        foreign_apps0 = [self.manger_app_id]
        foreign_assets0 = [self.underlying_asset_id]
        txn0 = ApplicationOptInTxn(user.address, params, self.app_id, app_args0, accounts=accounts0, foreign_apps=foreign_apps0, foreign_assets=foreign_assets0)
        
        return preamble_txns + TransactionGroup([txn0])
    
    def get_repay_borrow_txns(self, user, underlying_amount):
        """Returns a :class:`TransactionGroup` object representing a repay borrow group
        transaction against the algofi protocol. Sender repays borrowed underlying asset + interest to the protocol.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param underlying_amount: amount to repay
        :type underlying_amount: int
        :return: :class:`TransactionGroup` object representing a repay group transaction
        :rtype: :class:`TransactionGroup`
        """
        assert self.market_type != MarketType.VAULT
        
        params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(user.address, params, self.address, underlying_amount, self.underlying_asset_id)
        
        # application call
        app_args1 = [bytes(MARKET_STRINGS.repay_borrow)]
        accounts1 = [user.storage_address]
        foreign_apps1 = [self.manger_app_id]
        txn1 = ApplicationOptInTxn(user.address, params, self.app_id, app_args1, accounts=accounts1, foreign_apps=foreign_apps1)
        
        return TransactionGroup([txn0, txn1])
    
    def get_liquidate_txns(self, user, target_user, repay_amount, seize_collateral_market):
        """Returns a :class:`TransactionGroup` object representing a liquidate group
        transaction against the algofi protocol. Sender repays borrowed underlying asset + interest on behalf of
         the liquidatee and seizes their collateral in a specified market.

        :param user: account for the sender
        :type user: :class: `LendingUser`
        :param target_user: account for the liquidatee
        :type target_user: :class: `LendingUser`
        :param repay_amount: amount to repay
        :type repay_amount: int
        :param: seize_collateral_market: market to seize collateral in
        :type seize_collateral_market: :class: `Market`
        :return: :class:`TransactionGroup` object representing a liquidate group transaction
        :rtype: :class:`TransactionGroup`
        """
        assert self.market_type != MarketType.VAULT
        
        params = get_default_params(self.algod)
        
        preamble_txns = target_user.get_preamble_txns(params, self.app_id)
        
        # liquidate application call
        params.fee = 1000 + 1000 * preamble_txns.length()
        app_args0 = [bytes(MARKET_STRINGS.liquidate)]
        accounts0 = [target_user.storage_address]
        foreign_apps0 = [self.manger_app_id]
        txn0 = ApplicationOptInTxn(user.address, params, self.app_id, app_args0, accounts=accounts0, foreign_apps=foreign_apps0)
        
        # payment
        params.fee = 1000
        txn1 = get_payment_txn(user.address, params, self.address, repay_amount, self.underlying_asset_id)
        
        # seize collateral application call
        params.fee = 2000 + 1000 * preamble_txns.length()
        app_args2 = [bytes(MARKET_STRINGS.borrow)]
        accounts2 = [target_user.storage_address]
        foreign_apps2 = [seize_collateral_market.oracle.oracle_app_id]
        foreign_assets2 = [seize_collateral_market.underlying_asset_id]
        txn2 = ApplicationOptInTxn(user.address, params, seize_collateral_market.app_id, app_args2, accounts=accounts2, foreign_apps=foreign_apps2, foreign_assets=foreign_assets2)

        return preamble_txns + TransactionGroup([txn0, txn1, txn2])