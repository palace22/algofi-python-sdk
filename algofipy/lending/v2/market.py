# IMPORTS
from base64 import b64decode

from algosdk.encoding import encode_address
from algosdk.future.transaction import ApplicationNoOpTxn
from algosdk.logic import get_application_address

from .lending_config import MARKET_STRINGS, MarketType
from .oracle import Oracle

# INTERFACE
from ...asset_amount import AssetAmount
from ...globals import FIXED_3_SCALE_FACTOR, FIXED_6_SCALE_FACTOR
from ...state_utils import get_global_state
from ...transaction_utils import TransactionGroup, get_default_params, get_payment_txn
from ...utils import int_to_bytes, bytes_to_int


class RewardsProgramState:
    rewards_program_number_offset = 0
    rewards_per_second_offset = 8
    rewards_asset_id_offset = 16
    rewards_issued_offset = 24
    rewards_claimed_offset = 32
    rewards_state_length = 40

    def __init__(self, state, program_index):
        """The global state for a single rewards program on a given market

        :param state: raw global market state
        :type state: int
        :param program_index: the index of the rewards program on the market
        :type program_index: int
        """

        program_index_bytestr = int_to_bytes(program_index).decode()
        rewards_admin_key = MARKET_STRINGS.rewards_admin_prefix + program_index_bytestr
        rewards_program_state_key = (
            MARKET_STRINGS.rewards_program_state_prefix + program_index_bytestr
        )
        rewards_index_key = MARKET_STRINGS.rewards_index_prefix + program_index_bytestr

        self.rewards_admin = encode_address(b64decode(state.get(rewards_admin_key, "")))
        self.rewards_program_state = b64decode(state.get(rewards_program_state_key, ""))
        self.rewards_index = bytes_to_int(b64decode(state.get(rewards_index_key, 0)))
        self.rewards_program_number = bytes_to_int(
            self.rewards_program_state[
                self.rewards_program_number_offset : self.rewards_program_number_offset
                + 8
            ]
        )
        self.rewards_per_second = bytes_to_int(
            self.rewards_program_state[
                self.rewards_per_second_offset : self.rewards_per_second_offset + 8
            ]
        )
        self.rewards_asset_id = bytes_to_int(
            self.rewards_program_state[
                self.rewards_asset_id_offset : self.rewards_asset_id_offset + 8
            ]
        )
        self.rewards_issued = bytes_to_int(
            self.rewards_program_state[
                self.rewards_issued_offset : self.rewards_issued_offset + 8
            ]
        )
        self.rewards_claimed = bytes_to_int(
            self.rewards_program_state[
                self.rewards_claimed_offset : self.rewards_claimed_offset + 8
            ]
        )


class Market:
    local_min_balance = 471000

    def __init__(self, lending_client, market_config):
        """The python representation of an algofi lending market smart contract

        :param lending_client:
        :type lending_client: :class:`LendingClient`
        :param market_config: market config with market metadata
        :type market_config: :class:`MarketConfig`
        """

        self.lending_client = lending_client
        self.algod = self.lending_client.algod
        self.indexer = self.lending_client.indexer
        self.historical_indexer = self.lending_client.historical_indexer
        self.manager_app_id = lending_client.manager.app_id

        self.name = market_config.name
        self.app_id = market_config.app_id
        self.address = get_application_address(self.app_id)
        self.underlying_asset_id = market_config.underlying_asset_id
        self.b_asset_id = market_config.b_asset_id
        self.market_type = market_config.market_type
        self.created_at_round = self.indexer.applications(self.app_id)["application"][
            "created-at-round"
        ]

        self.load_state()

    def load_state(self, block=None):
        """
        Loads market state from the blockchain

        :param block: block at which to query market state
        :type block: int, optional
        :rtype: None
        """

        indexer = self.historical_indexer if block else self.indexer
        state = get_global_state(
            indexer, self.app_id, decode_byte_values=False, block=block
        )

        # parameters
        self.borrow_factor = state.get(MARKET_STRINGS.borrow_factor, 0)
        self.collateral_factor = state.get(MARKET_STRINGS.collateral_factor, 0)
        self.flash_loan_fee = state.get(MARKET_STRINGS.flash_loan_fee, 0)
        self.flash_loan_protocol_fee = state.get(
            MARKET_STRINGS.flash_loan_protocol_fee, 0
        )
        self.max_flash_loan_ratio = state.get(MARKET_STRINGS.max_flash_loan_ratio, 0)
        self.liquidation_incentive = state.get(MARKET_STRINGS.liquidation_incentive, 0)
        self.liquidation_fee = state.get(MARKET_STRINGS.liquidation_fee, 0)
        self.reserve_factor = state.get(MARKET_STRINGS.reserve_factor, 0)
        self.underlying_supply_cap = state.get(MARKET_STRINGS.underlying_supply_cap, 0)
        self.underlying_borrow_cap = state.get(MARKET_STRINGS.underlying_borrow_cap, 0)

        # interest rate model
        self.base_interest_rate = state.get(MARKET_STRINGS.base_interest_rate, 0)
        self.base_interest_slope = state.get(MARKET_STRINGS.base_interest_slope, 0)
        self.quadratic_interest_amplification_factor = state.get(
            MARKET_STRINGS.quadratic_interest_amplification_factor, 0
        )
        self.target_utilization_ratio = state.get(
            MARKET_STRINGS.target_utilization_ratio, 0
        )

        # oracle
        self.oracle = Oracle(
            self.indexer,
            self.historical_indexer,
            state.get(MARKET_STRINGS.oracle_app_id, 0),
            b64decode(
                state.get(MARKET_STRINGS.oracle_price_field_name, "price")
            ).decode("utf-8"),
            state.get(MARKET_STRINGS.oracle_price_scale_factor, 0),
        )
        self.oracle.load_price(block=block)

        # balance
        self.underlying_cash = state.get(MARKET_STRINGS.underlying_cash, 0)
        self.underlying_borrowed = state.get(MARKET_STRINGS.underlying_borrowed, 0)
        self.underlying_reserves = state.get(MARKET_STRINGS.underlying_reserves, 0)
        self.borrow_share_circulation = state.get(
            MARKET_STRINGS.borrow_share_circulation, 0
        )
        self.b_asset_circulation = state.get(MARKET_STRINGS.b_asset_circulation, 0)
        self.active_b_asset_collateral = state.get(
            MARKET_STRINGS.active_b_asset_collateral, 0
        )
        self.underlying_protocol_reserve = state.get(
            MARKET_STRINGS.underlying_protocol_reserve, 0
        )

        # interest
        self.latest_time = state.get(MARKET_STRINGS.latest_time, 0)
        self.borrow_index = state.get(MARKET_STRINGS.borrow_index, 0)
        self.implied_borrow_index = state.get(MARKET_STRINGS.implied_borrow_index, 0)

        # calculated values
        self.total_supplied = AssetAmount(
            self.get_underlying_supplied()
            / (
                10
                ** self.lending_client.algofi_client.assets[
                    self.underlying_asset_id
                ].decimals
            ),
            self.underlying_to_usd(self.get_underlying_supplied()),
        )

        self.total_borrowed = AssetAmount(
            self.underlying_borrowed
            / (
                10
                ** self.lending_client.algofi_client.assets[
                    self.underlying_asset_id
                ].decimals
            ),
            self.underlying_to_usd(self.underlying_borrowed),
        )

        self.supply_apr, self.borrow_apr = self.get_aprs(
            self.total_supplied.underlying, self.total_borrowed.underlying
        )

        # rewards
        self.rewards_escrow_account = encode_address(
            b64decode(state.get(MARKET_STRINGS.rewards_escrow_account, ""))
        )
        self.rewards_latest_time = state.get(MARKET_STRINGS.rewards_latest_time, 0)
        self.max_rewards_program_index = 1
        self.rewards_programs = []
        for i in range(self.max_rewards_program_index + 1):
            self.rewards_programs.append(RewardsProgramState(state, i))

    # GETTERS

    def get_underlying_supplied(self):
        """Returns the total amount of underlying asset that has been supplied to the market,
        including the amount that has been borrowed

        :return: Supplied amount in base unit terms
        :rtype: int
        """

        if self.market_type == MarketType.STBL:
            return self.underlying_cash
        else:
            return (
                self.underlying_borrowed
                + self.underlying_cash
                - self.underlying_reserves
            )

    def get_aprs(self, total_supplied, total_borrowed):
        """Return the supply and borrow APR for the market.

        :param total_supplied: total amount underlying assets supplied
        :type total_supplied: int
        :param total_borrowed: total amount underlying assets borrowed
        :type total_borrowed: int
        :return: (supply_apr, borrow_apr)
        :rtype: (float, float)
        """

        borrow_utilization = (
            0 if total_supplied == 0 else total_borrowed / total_supplied
        )
        borrow_apr = self.base_interest_rate / FIXED_6_SCALE_FACTOR
        borrow_apr += (
            borrow_utilization * self.base_interest_slope / FIXED_6_SCALE_FACTOR
        )
        if borrow_utilization > (self.target_utilization_ratio / FIXED_6_SCALE_FACTOR):
            borrow_apr += self.quadratic_interest_amplification_factor * (
                (
                    borrow_utilization
                    - self.target_utilization_ratio / FIXED_6_SCALE_FACTOR
                )
                ** 2
            )
        supply_apr = (
            borrow_apr
            * borrow_utilization
            * (1 - self.reserve_factor / FIXED_6_SCALE_FACTOR)
        )
        return supply_apr, borrow_apr

    # CONVERSIONS

    def underlying_to_usd(self, amount):
        """Converts underlying to usd

        :param amount: underlying asset amount
        :type amount: int
        :return: dollarized amount
        :rtype: int
        """

        return (amount * self.oracle.raw_price) / (
            self.oracle.scale_factor * FIXED_3_SCALE_FACTOR
        )

    def b_asset_to_asset_amount(self, amount):
        """Converts b asset amount to underlying amount

        :param amount: b asset amount
        :type amount: int
        :return: underlying asset amount
        :rtype: int
        """

        if amount == 0:
            return AssetAmount(0, 0)
        raw_underlying_amount = int(
            amount * self.get_underlying_supplied() // self.b_asset_circulation
        )
        usd_amount = self.underlying_to_usd(raw_underlying_amount)
        return AssetAmount(raw_underlying_amount, usd_amount)

    def borrow_shares_to_asset_amount(self, amount):
        """Converts borrow shares to underlying borrowed amount.

        :param amount: borrow shares amount
        :type amount: int
        :return: underlying borrowed amount
        :rtype: int
        """

        if amount == 0:
            return AssetAmount(0, 0)
        raw_underlying_amount = int(
            amount * self.underlying_borrowed // self.borrow_share_circulation
        )
        usd_amount = self.underlying_to_usd(raw_underlying_amount)
        return AssetAmount(raw_underlying_amount, usd_amount)

    def underlying_to_b_asset(self, amount):
        """Convert underlying asset amount to b asset amount.

        :param amount: underlying asset amount
        :type amount: int
        :return: b asset amount
        :rtype: int
        """

        return amount * self.b_asset_circulation / self.get_underlying_supplied()

    # TRANSACTION BUILDERS
    def get_b_asset_opt_in_txn(self, user, params=None):
        """Returns a :class:`AssetTransferTxn` object representing a transfer of zero units of the b asset.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`AssetTransferTxn` of underlying asset with 0 amount from user to self
        :rtype: :class:`AssetTransferTxn`
        """

        assert self.market_type != MarketType.VAULT
        if params is None:
            params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(user.address, params, user.address, 0, self.b_asset_id)

        return txn0

    def get_underlying_asset_opt_in_txn(self, user, params=None):
        """Returns a :class:`AssetTransferTxn` object representing a transfer of zero units of the market underlying asset.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`AssetTransferTxn` of underlying asset with 0 amount from user to self
        :rtype: :class:`AssetTransferTxn`
        """

        assert self.market_type != MarketType.VAULT
        if params is None:
            params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(
            user.address, params, user.address, 0, self.underlying_asset_id
        )

        return txn0

    def get_mint_txns(self, user, underlying_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing a mint bank asset group
        transaction against the algofi protocol. Sender mints bank asset by sending underlying asset
        to the account address of the market application which sends back the bank asset.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param underlying_amount: amount of underlying asset to use in minting
        :type underlying_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a mint group transaction of size 2
        :rtype: :class:`TransactionGroup`
        """

        assert self.market_type != MarketType.VAULT
        if params is None:
            params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(
            user.address,
            params,
            self.address,
            underlying_amount,
            self.underlying_asset_id,
        )

        # application call
        params.fee = 3000
        app_args1 = [bytes(MARKET_STRINGS.mint_b_asset, "utf-8")]
        foreign_apps1 = [self.manager_app_id]
        foreign_assets1 = [self.b_asset_id]
        txn1 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args1,
            foreign_apps=foreign_apps1,
            foreign_assets=foreign_assets1,
        )

        return TransactionGroup([txn0, txn1])

    def get_add_underlying_collateral_txns(self, user, underlying_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing an add collateral group
        transaction against the algofi protocol. Sender adds underlying asset amount to collateral by sending
        it to the account address of the market application that updates user active collateral.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param underlying_amount: amount of underlying asset to add to collateral
        :type underlying_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an add collateral group transaction of size 2
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # payment
        receiver = (
            self.address
            if self.market_type != MarketType.VAULT
            else user.storage_address
        )
        txn0 = get_payment_txn(
            user.address, params, receiver, underlying_amount, self.underlying_asset_id
        )

        params.fee = 2000
        # application call
        app_args1 = [bytes(MARKET_STRINGS.add_underlying_collateral, "utf-8")]
        accounts1 = [user.storage_address]
        foreign_apps1 = [self.manager_app_id]
        txn1 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args1,
            accounts=accounts1,
            foreign_apps=foreign_apps1,
        )

        return TransactionGroup([txn0, txn1])

    def get_add_b_asset_collateral_txns(self, user, b_asset_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing an add collateral group
        transaction against the algofi protocol. Sender adds bank asset amount to collateral by sending
        them to the account address of the market application that generates the bank assets.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param b_asset_amount: amount of bank asset to add to collateral
        :type b_asset_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an add collateral group transaction of size 2
        :rtype: :class:`TransactionGroup`
        """

        assert self.market_type != MarketType.VAULT

        if params is None:
            params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(
            user.address, params, self.address, b_asset_amount, self.b_asset_id
        )

        params.fee = 2000
        # application call
        app_args1 = [bytes(MARKET_STRINGS.add_b_asset_collateral, "utf-8")]
        accounts1 = [user.storage_address]
        foreign_apps1 = [self.manager_app_id]
        txn1 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args1,
            accounts=accounts1,
            foreign_apps=foreign_apps1,
        )

        return TransactionGroup([txn0, txn1])

    def get_remove_underlying_collateral_txns(
        self, user, underlying_amount, params=None
    ):
        """Returns a :class:`TransactionGroup` object representing a remove collateral group
        transaction against the algofi protocol. Sender reclaims underlying collateral asset by reducing their active
        collateral.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param underlying_amount: amount of underlying asset to remove
        :type underlying_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a remove collateral group transaction
            of size (preamble_length + 1)
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        preamble_txns = user.get_preamble_txns(params, self.app_id)

        # application call
        params.fee = (
            2000 + 1000 * preamble_txns.length()
            if self.market_type != MarketType.VAULT
            else 3000 + 1000 * preamble_txns.length()
        )
        app_args0 = [
            bytes(MARKET_STRINGS.remove_underlying_collateral, "utf-8"),
            int_to_bytes(underlying_amount),
        ]
        accounts0 = [user.storage_address]
        foreign_apps0 = [self.manager_app_id]
        foreign_assets0 = [self.underlying_asset_id]
        txn0 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args0,
            accounts=accounts0,
            foreign_apps=foreign_apps0,
            foreign_assets=foreign_assets0,
        )

        return preamble_txns + TransactionGroup([txn0])

    def get_remove_b_asset_collateral_txns(self, user, b_asset_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing a remove collateral group
        transaction against the algofi protocol. Sender reclaims collateral bank asset by reducing their active
        collateral.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param b_asset_amount: amount of underlying asset to remove
        :type b_asset_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a remove collateral group transaction
        :rtype: :class:`TransactionGroup`
        """

        assert self.market_type != MarketType.VAULT

        if params is None:
            params = get_default_params(self.algod)

        preamble_txns = user.get_preamble_txns(params, self.app_id)

        # application call
        params.fee = 2000 + 1000 * preamble_txns.length()
        app_args0 = [
            bytes(MARKET_STRINGS.remove_b_asset_collateral, "utf-8"),
            int_to_bytes(b_asset_amount),
        ]
        accounts0 = [user.storage_address]
        foreign_apps0 = [self.manager_app_id]
        foreign_assets0 = [self.b_asset_id]
        txn0 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args0,
            accounts=accounts0,
            foreign_apps=foreign_apps0,
            foreign_assets=foreign_assets0,
        )

        return preamble_txns + TransactionGroup([txn0])

    def get_burn_txns(self, user, b_asset_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing a burn group
        transaction against the algofi protocol. Sender reclaims underlying collateral asset by burning bank asset.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param b_asset_amount: amount of underlying asset to remove
        :type b_asset_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a burn group transaction of size 2
        :rtype: :class:`TransactionGroup`
        """

        assert self.market_type != MarketType.VAULT

        if params is None:
            params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(
            user.address, params, self.address, b_asset_amount, self.b_asset_id
        )

        # application call
        app_args1 = [bytes(MARKET_STRINGS.burn_b_asset, "utf-8")]
        foreign_apps1 = [self.manager_app_id]
        foreign_assets1 = [self.underlying_asset_id]
        params.fee = 3000
        txn1 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args1,
            foreign_apps=foreign_apps1,
            foreign_assets=foreign_assets1,
        )

        return TransactionGroup([txn0, txn1])

    def get_borrow_txns(self, user, underlying_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing a borrow group
        transaction against the algofi protocol. Sender borrows underlying asset against their
        collateral in the protocol.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param underlying_amount: amount to borrow
        :type underlying_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a borrow group transaction of size (preamble_length + 1)
        :rtype: :class:`TransactionGroup`
        """

        assert (self.market_type != MarketType.VAULT) and (
            self.market_type != MarketType.LP
        )

        if params is None:
            params = get_default_params(self.algod)

        preamble_txns = user.get_preamble_txns(params, self.app_id)
        # application call
        params.fee = 2000 + 1000 * preamble_txns.length()
        app_args0 = [
            bytes(MARKET_STRINGS.borrow, "utf-8"),
            int_to_bytes(underlying_amount),
        ]
        accounts0 = [user.storage_address]
        foreign_apps0 = [self.manager_app_id]
        foreign_assets0 = [self.underlying_asset_id]
        txn0 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args0,
            accounts=accounts0,
            foreign_apps=foreign_apps0,
            foreign_assets=foreign_assets0,
        )

        return preamble_txns + TransactionGroup([txn0])

    def get_repay_borrow_txns(self, user, underlying_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing a repay borrow group
        transaction against the algofi protocol. Sender repays borrowed underlying asset + interest to the protocol.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param underlying_amount: amount to repay
        :type underlying_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a repay group transaction of size 2
        :rtype: :class:`TransactionGroup`
        """

        assert (self.market_type != MarketType.VAULT) and (
            self.market_type != MarketType.LP
        )

        if params is None:
            params = get_default_params(self.algod)

        # payment
        txn0 = get_payment_txn(
            user.address,
            params,
            self.address,
            underlying_amount,
            self.underlying_asset_id,
        )

        # application call
        params.fee = 3000
        app_args1 = [bytes(MARKET_STRINGS.repay_borrow, "utf-8")]
        accounts1 = [user.storage_address]
        foreign_apps1 = [self.manager_app_id]
        foreign_assets = [self.underlying_asset_id]
        txn1 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args1,
            accounts=accounts1,
            foreign_apps=foreign_apps1,
            foreign_assets=foreign_assets,
        )

        return TransactionGroup([txn0, txn1])

    def get_liquidate_txns(
        self, user, target_user, repay_amount, seize_collateral_market, params=None
    ):
        """Returns a :class:`TransactionGroup` object representing a liquidate group
        transaction against the algofi protocol. Sender repays borrowed underlying asset + interest on behalf of
        the liquidatee and seizes their collateral in a specified market.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param target_user: account for the liquidatee
        :type target_user: :class:`LendingUser`
        :param repay_amount: amount to repay
        :type repay_amount: int
        :param: seize_collateral_market: market to seize collateral in
        :type seize_collateral_market: :class:`Market`
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a liquidate group transaction of size (preamble_length + 3)
        :rtype: :class:`TransactionGroup`
        """

        assert self.market_type != MarketType.VAULT

        if params is None:
            params = get_default_params(self.algod)

        preamble_txns = target_user.get_preamble_txns(params, self.app_id, user.address)

        # liquidate application call
        params.fee = 1000 + 1000 * preamble_txns.length()
        app_args0 = [bytes(MARKET_STRINGS.liquidate, "utf-8")]
        accounts0 = [
            target_user.storage_address,
            get_application_address(seize_collateral_market.app_id),
        ]
        foreign_apps0 = [self.manager_app_id, seize_collateral_market.app_id]
        txn0 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args=app_args0,
            accounts=accounts0,
            foreign_apps=foreign_apps0,
        )

        # payment
        params.fee = 1000
        txn1 = get_payment_txn(
            user.address, params, self.address, repay_amount, self.underlying_asset_id
        )

        # seize collateral application call
        params.fee = 2000 + 1000 * preamble_txns.length()
        app_args2 = [bytes(MARKET_STRINGS.seize_collateral, "utf-8")]
        accounts2 = [target_user.storage_address, get_application_address(self.app_id)]
        foreign_apps2 = [
            seize_collateral_market.oracle.app_id,
            self.manager_app_id,
            self.app_id,
        ]
        foreign_assets2 = [seize_collateral_market.b_asset_id]
        txn2 = ApplicationNoOpTxn(
            user.address,
            params,
            seize_collateral_market.app_id,
            app_args=app_args2,
            accounts=accounts2,
            foreign_apps=foreign_apps2,
            foreign_assets=foreign_assets2,
        )

        return preamble_txns + TransactionGroup([txn0, txn1, txn2])

    def get_claim_rewards_txns(self, user, program_index, params=None):
        """Returns a :class:`TransactionGroup` object representing a claim rewards group
        transaction against the algofi protocol. Sender claims accrued rewards from a specified rewards program.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param program_index: specific program for which the rewards are being claimed
        :type program_index: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a claim rewards group transaction of size 1
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # application call
        params.fee = 3000
        foreign_apps = [self.manager_app_id]
        accounts = [user.storage_address, self.rewards_escrow_account]
        app_args = [
            bytes(MARKET_STRINGS.claim_rewards, "utf-8"),
            int_to_bytes(program_index),
        ]
        foreign_assets = [self.rewards_programs[program_index].rewards_asset_id]
        txn0 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args,
            accounts=accounts,
            foreign_apps=foreign_apps,
            foreign_assets=foreign_assets,
        )

        return TransactionGroup([txn0])
