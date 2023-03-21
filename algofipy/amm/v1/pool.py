# IMPORTS

# external
import time
import math
from algosdk.logic import get_application_address
from algosdk.transaction import (
    LogicSigAccount,
    LogicSigTransaction,
    OnComplete,
    StateSchema,
    ApplicationCreateTxn,
    ApplicationOptInTxn,
    ApplicationNoOpTxn,
    OnComplete,
)

# local
from .amm_config import (
    PoolStatus,
    Network,
    get_validator_index,
    get_approval_program_by_pool_type,
    get_clear_state_program,
    PoolType,
    TESTNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID,
    MAINNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID,
    POOL_STRINGS,
    MANAGER_STRINGS,
    PARAMETER_SCALE_FACTOR,
    MAINNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID,
    TESTNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID,
    CONSTANT_PRODUCT_LENDING_POOLS_ASSET_PAIR_TO_APP_ID,
    NANOSWAP_LENDING_POOLS_ASSET_PAIR_TO_APP_ID,
    NANOSWAP_LENDING_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID,
    CONSTANT_PRODUCT_LENDING_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID,
    TESTNET_NANOSWAP_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID,
    MAINNET_NANOSWAP_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID,
    AMMEndpoints,
)
from .asset import Asset
from .balance_delta import BalanceDelta
from .logic_sig_generator import generate_logic_sig
from .stable_swap_math import get_D, get_y
from ...transaction_utils import TransactionGroup, get_payment_txn, get_default_params
from ...state_utils import get_local_state_at_app, get_global_state
from ...globals import FIXED_12_SCALE_FACTOR
from ...utils import int_to_bytes

# INTERFACE


class Pool:
    last_update = 0
    def __init__(self, amm_client, pool_type, asset1, asset2):
        """Constructor method for :class:`Pool`

        :param amm_client: a :class:`AMMClient` object for interacting with the AMM
        :type amm_client: :class:`AMMClient`
        :param pool_type: a :class:`PoolType` object for the type of pool (e.g. 30bp, 100bp fee)
        :type pool_type: :class:`PoolType`
        :param asset1: a :class:`Asset` representing the first asset of the pool
        :type asset1: :class:`Asset`
        :param asset2: a :class:`Asset` representing the second asset of the pool
        :type asset2: :class:`Asset`
        """

        if asset1.asset_id >= asset2.asset_id:
            raise Exception(
                "Invalid asset ordering. Asset 1 id must be less than asset 2 id."
            )

        # load nodes + network data
        self.amm_client = amm_client
        self.algod = self.amm_client.algod
        self.indexer = self.amm_client.indexer
        self.historical_indexer = self.amm_client.historical_indexer
        self.network = self.amm_client.network

        # load generic pool metadata
        self.pool_type = pool_type
        self.asset1 = asset1
        self.asset2 = asset2
        self.validator_index = get_validator_index(self.network, pool_type)

        # get pool app id using hard-coded dictionaries for NANOSWAP + LENDING_POOLS and on-chain logic sigs for constant product AMM pools
        self.application_id = None
        key = (asset1.asset_id, asset2.asset_id)
        if pool_type == PoolType.NANOSWAP:
            self.pool_status = PoolStatus.ACTIVE
            self.application_id = (
                TESTNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID
                if self.network == Network.TESTNET
                else MAINNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID
            )[key]
            self.manager_application_id = (
                TESTNET_NANOSWAP_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID
                if self.network == Network.TESTNET
                else MAINNET_NANOSWAP_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID
            )[key]
        elif pool_type == PoolType.NANOSWAP_LENDING_POOL:
            if self.network == Network.TESTNET:
                raise Exception("Lending Pool is not on testnet")
            self.pool_status = PoolStatus.ACTIVE
            self.application_id = NANOSWAP_LENDING_POOLS_ASSET_PAIR_TO_APP_ID[key]
            self.manager_application_id = (
                NANOSWAP_LENDING_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID[key]
            )

        elif pool_type == PoolType.CONSTANT_PRODUCT_25BP_FEE_LENDING_POOL:
            if self.network == Network.TESTNET:
                raise Exception("Lending Pool is not on testnet")
            self.pool_status = PoolStatus.ACTIVE
            self.application_id = CONSTANT_PRODUCT_LENDING_POOLS_ASSET_PAIR_TO_APP_ID[
                key
            ]
            self.manager_application_id = (
                CONSTANT_PRODUCT_LENDING_POOLS_ASSET_PAIR_TO_MANAGER_APP_ID[key]
            )
        else:
            # get local state
            self.manager_application_id = (
                MAINNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID
                if self.network == Network.MAINNET
                else TESTNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID
            )
            self.manager_address = get_application_address(self.manager_application_id)
            self.logic_sig = LogicSigAccount(
                generate_logic_sig(
                    asset1.asset_id,
                    asset2.asset_id,
                    self.manager_application_id,
                    self.validator_index,
                )
            )
            try:
                logic_sig_local_state = get_local_state_at_app(
                    self.indexer, self.logic_sig.address(), self.manager_application_id
                )
                self.pool_status = PoolStatus.ACTIVE
            except:
                logic_sig_local_state = None
                self.pool_status = PoolStatus.UNINITIALIZED

            if logic_sig_local_state:

                if (
                    (
                        logic_sig_local_state[MANAGER_STRINGS.registered_asset_1_id]
                        != asset1.asset_id
                    )
                    or (
                        logic_sig_local_state[MANAGER_STRINGS.registered_asset_2_id]
                        != asset2.asset_id
                    )
                    or (
                        logic_sig_local_state[MANAGER_STRINGS.validator_index]
                        != self.validator_index
                    )
                ):
                    raise Exception("Logic sig state does not match as expected")

                self.application_id = logic_sig_local_state[
                    MANAGER_STRINGS.registered_pool_id
                ]

        # if application id has been set, then either nanoswap pool or constant product pool is active
        if self.application_id:
            self.address = get_application_address(self.application_id)
            self.created_at_round = self.indexer.applications(self.application_id)[
                "application"
            ]["created-at-round"]
            # save down pool metadata
            pool_state = get_global_state(self.indexer, self.application_id)
            self.lp_asset_id = pool_state[POOL_STRINGS.lp_id]
            self.lp_asset = Asset(self.amm_client, self.lp_asset_id)
            self.admin = pool_state[POOL_STRINGS.admin]
            self.reserve_factor = pool_state[POOL_STRINGS.reserve_factor]
            self.flash_loan_fee = pool_state[POOL_STRINGS.flash_loan_fee]
            self.max_flash_loan_ratio = pool_state[POOL_STRINGS.max_flash_loan_ratio]
            self.swap_fee = pool_state[POOL_STRINGS.swap_fee_pct_scaled_var] / 1e6

            # additionally save down nanoswap metadata if applicable
            if (self.pool_type == PoolType.NANOSWAP) or (
                self.pool_type == PoolType.NANOSWAP_LENDING_POOL
            ):
                self.initial_amplification_factor = pool_state.get(
                    POOL_STRINGS.initial_amplification_factor, 0
                )
                self.future_amplification_factor = pool_state.get(
                    POOL_STRINGS.future_amplification_factor, 0
                )
                self.initial_amplification_factor_time = pool_state.get(
                    POOL_STRINGS.initial_amplification_factor_time, 0
                )
                self.future_amplification_factor_time = pool_state.get(
                    POOL_STRINGS.future_amplification_factor_time, 0
                )
                status = self.algod.status()
                last_round = status["last-round"]
                block = self.algod.block_info(last_round)
                timestamp = block["block"]["ts"]
                self.t = timestamp

            # lending nanoswap pool (moving ratio pool) metadata
            if (self.pool_type == PoolType.NANOSWAP_LENDING_POOL):
                self.target_ratio_adjustment_start_time = pool_state.get(
                    POOL_STRINGS.target_ratio_adjustment_start_time, 0
                )
                self.target_ratio_adjustment_end_time = pool_state.get(
                    POOL_STRINGS.target_ratio_adjustment_end_time, 0
                )
                self.initial_target_asset1_to_asset2_ratio = pool_state.get(
                    POOL_STRINGS.initial_target_asset1_to_asset2_ratio, 0
                )
                self.current_target_asset1_to_asset2_ratio = pool_state.get(
                    POOL_STRINGS.current_target_asset1_to_asset2_ratio, 0
                )
                self.goal_target_asset1_to_asset2_ratio = pool_state.get(
                    POOL_STRINGS.goal_target_asset1_to_asset2_ratio, 0
                )

            # refresh state
            self.load_state()

    def refresh_metadata(self):
        """Refresh the metadata of the pool (e.g. if now initialized)."""

        if (self.pool_type != PoolType.NANOSWAP) and (
            self.pool_type != PoolType.NANOSWAP_LENDING_POOL
        ):
            try:
                logic_sig_local_state = get_local_state_at_app(
                    self.indexer, self.logic_sig.address(), self.manager_application_id
                )
                self.pool_status = PoolStatus.ACTIVE
            except:
                logic_sig_local_state = None
                self.pool_status = PoolStatus.UNINITIALIZED

            if logic_sig_local_state:

                if (
                    (
                        logic_sig_local_state[MANAGER_STRINGS.registered_asset_1_id]
                        != self.asset1.asset_id
                    )
                    or (
                        logic_sig_local_state[MANAGER_STRINGS.registered_asset_2_id]
                        != self.asset2.asset_id
                    )
                    or (
                        logic_sig_local_state[MANAGER_STRINGS.validator_index]
                        != self.validator_index
                    )
                ):
                    raise Exception("Logic sig state does not match as expected")

                self.application_id = logic_sig_local_state[
                    MANAGER_STRINGS.registered_pool_id
                ]

                self.address = get_application_address(self.application_id)
                # get global state
                pool_state = get_global_state(self.indexer, self.application_id)
                self.lp_asset_id = pool_state[POOL_STRINGS.lp_id]
                self.lp_asset = Asset(self.amm_client, self.lp_asset_id)
                self.admin = pool_state[POOL_STRINGS.admin]
                self.reserve_factor = pool_state[POOL_STRINGS.reserve_factor]
                self.flash_loan_fee = pool_state[POOL_STRINGS.flash_loan_fee]
                self.max_flash_loan_ratio = pool_state[
                    POOL_STRINGS.max_flash_loan_ratio
                ]
        else:
            pool_state = get_global_state(self.indexer, self.application_id)
            self.initial_amplification_factor = pool_state.get(
                POOL_STRINGS.initial_amplification_factor, 0
            )
            self.future_amplification_factor = pool_state.get(
                POOL_STRINGS.future_amplification_factor, 0
            )
            self.initial_amplification_factor_time = pool_state.get(
                POOL_STRINGS.initial_amplification_factor_time, 0
            )
            self.future_amplification_factor_time = pool_state.get(
                POOL_STRINGS.future_amplification_factor_time, 0
            )
            status = self.algod.status()
            last_round = status["last-round"]
            block = self.algod.block_info(last_round)
            timestamp = block["block"]["ts"]
            self.t = timestamp

    def load_state(self, last_update=None, block=None):
        """Refresh the global state of the pool

        :param block: block at which to query historical state
        :type block: int, optional
        """
        if not last_update or last_update != self.last_update:
            self.last_update = last_update

            # load pool state
            indexer_client = self.historical_indexer if block else self.indexer
            pool_state = get_global_state(indexer_client, self.application_id, block=block)
            self.asset1_balance = pool_state[POOL_STRINGS.balance_1]
            self.asset2_balance = pool_state[POOL_STRINGS.balance_2]
            self.lp_circulation = pool_state[POOL_STRINGS.lp_circulation]
            self.asset1_reserve = pool_state[POOL_STRINGS.asset1_reserve]
            self.asset2_reserve = pool_state[POOL_STRINGS.asset2_reserve]
            self.latest_time = pool_state[POOL_STRINGS.latest_time]
            self.cumsum_time_weighted_asset1_to_asset2_price = pool_state[
                POOL_STRINGS.cumsum_time_weighted_asset1_to_asset2_price
            ]
            self.cumsum_time_weighted_asset2_to_asset1_price = pool_state[
                POOL_STRINGS.cumsum_time_weighted_asset2_to_asset1_price
            ]
            self.cumsum_volume_asset1 = pool_state[POOL_STRINGS.cumsum_volume_asset1]
            self.cumsum_volume_asset2 = pool_state[POOL_STRINGS.cumsum_volume_asset2]
            self.cumsum_volume_weighted_asset1_to_asset2_price = pool_state[
                POOL_STRINGS.cumsum_volume_weighted_asset1_to_asset2_price
            ]
            self.cumsum_volume_weighted_asset2_to_asset1_price = pool_state[
                POOL_STRINGS.cumsum_volume_weighted_asset2_to_asset1_price
            ]
            self.cumsum_fees_asset1 = pool_state[POOL_STRINGS.cumsum_fees_asset1]
            self.cumsum_fees_asset2 = pool_state[POOL_STRINGS.cumsum_fees_asset2]

    def refresh_lp_token_price(self):
        """Refresh the dollar price of the LP token for this pool"""

        self.lp_asset.refresh_price()

    def get_pool_price(self, asset_id):
        """Gets the price of the pool in terms of the asset with given asset_id
        :param asset_id: asset id of the asset to price
        :type asset_id: int
        :return: price of pool in terms of asset with given asset_id
        :rtype: float
        """

        if asset_id == self.asset1.asset_id:
            return (
                self.asset2_balance
                / self.asset1_balance
                * 10 ** (self.asset1.decimals - self.asset2.decimals)
            )
        elif asset_id == self.asset2.asset_id:
            return (
                self.asset1_balance
                / self.asset2_balance
                * 10 ** (self.asset2.decimals - self.asset1.decimals)
            )
        else:
            raise Exception("Invalid asset id")

    def sign_txn_with_logic_sig(self, transaction):
        """Returns input transaction signed with logic sig of pool

        :param transaction: a :class:`Transaction` to sign
        :type transaction: :class:`Transaction`
        :return: transaction signed with logic sig of pool
        :rtype: :class:`SignedTransaction`
        """
        assert (self.pool_type != PoolType.NANOSWAP) and (
            self.pool_type != PoolType.NANOSWAP_LENDING_POOL
        ), "Nanoswap pools are not compatible with manager logic sigs"
        return LogicSigTransaction(transaction, self.logic_sig)

    def get_create_pool_txn(self, sender, params=None):
        """Returns unsigned CreatePool transaction with given sender

        :param sender: sender
        :type sender: str
        :return: unsigned CreatePool transaction with given sender
        :rtype: :class:`ApplicationCreateTxn`
        """
        if (self.pool_type == PoolType.NANOSWAP) and (
            self.pool_type != PoolType.NANOSWAP_LENDING_POOL
        ):
            raise Exception("Nanoswap pool creation is not supported")

        if self.pool_status == PoolStatus.ACTIVE:
            raise Exception(
                "Pool already created and active - cannot generate create pool txn"
            )

        if params is None:
            params = get_default_params(self.algod)

        approval_program = get_approval_program_by_pool_type(
            self.pool_type, self.network
        )
        clear_state_program = get_clear_state_program()

        global_schema = StateSchema(num_uints=32, num_byte_slices=4)
        local_schema = StateSchema(num_uints=0, num_byte_slices=0)

        txn0 = ApplicationCreateTxn(
            sender=sender,
            sp=params,
            on_complete=OnComplete.NoOpOC,
            approval_program=approval_program,
            clear_program=clear_state_program,
            global_schema=global_schema,
            local_schema=local_schema,
            app_args=[
                int_to_bytes(self.asset1.asset_id),
                int_to_bytes(self.asset2.asset_id),
                int_to_bytes(self.validator_index),
            ],
            foreign_apps=[self.manager_application_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
            extra_pages=3,
        )

        return TransactionGroup([txn0])

    def get_initialize_pool_txns(self, sender, pool_app_id, params=None):
        """Get group transaction for initializing the pool. First, the manager is
        funded (which funds the pool contract (for opting into assets, creating LP token)
        via an inner payment txn. Then, the logic sig is funded to opt into manager.
        After, the sender calls the initialize function on the pool. This transaction
        "registers" the pool with the manager so it is searchable via SDK.

        :param sender: sender
        :type sender: str
        :param pool_app_id: application id of the pool to initialize
        :type pool_app_id: int
        :return: unsigned group transaction :class:`TransactionGroup` with sender for initializing pool
        :rtype: :class:`TransactionGroup`
        """

        if self.pool_status == PoolStatus.ACTIVE:
            raise Exception("Pool already active - cannot generate initialize pool txn")

        if params is None:
            params = get_default_params(self.algod)

        # fund manager
        if self.network == Network.MAINNET:
            txn0 = get_payment_txn(sender, params, self.manager_address, amount=400000)
        else:
            txn0 = get_payment_txn(sender, params, self.manager_address, amount=500000)

        # fund logic sig
        if self.network == Network.MAINNET:
            txn1 = get_payment_txn(
                sender, params, self.logic_sig.address(), amount=450000
            )
        else:
            txn1 = get_payment_txn(
                sender, params, self.logic_sig.address(), amount=835000
            )

        # opt logic sig into manager
        params.fee = 2000
        txn2 = ApplicationOptInTxn(
            sender=self.logic_sig.address(),
            sp=params,
            index=self.manager_application_id,
            app_args=[
                int_to_bytes(self.asset1.asset_id),
                int_to_bytes(self.asset2.asset_id),
                int_to_bytes(self.validator_index),
            ],
            accounts=[get_application_address(pool_app_id)],
            foreign_apps=[pool_app_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        # call pool initialize fcn
        params.fee = 4000
        foreign_assets = (
            [self.asset2.asset_id]
            if self.asset1.asset_id == 1
            else [self.asset1.asset_id, self.asset2.asset_id]
        )
        txn3 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=pool_app_id,
            app_args=[bytes(POOL_STRINGS.initialize_pool, "utf-8")],
            foreign_apps=[self.manager_application_id],
            foreign_assets=foreign_assets,
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        return TransactionGroup([txn0, txn1, txn2, txn3])

    def get_lp_token_opt_in_txn(self, sender, params=None):
        """Get lp token opt in transaction for the given sender

        :param sender: sender
        :type sender: str
        :return: lp token opt in transaction for the given sender
        :rtype: :class:`PaymentTxn` or :class:`AssetTransferTxn`
        """
        if params is None:
            params = get_default_params(self.algod)
        return get_payment_txn(
            sender, params, sender, amount=int(0), asset_id=self.lp_asset_id
        )

    def get_pool_txns(
        self,
        sender,
        asset1_amount,
        asset2_amount,
        maximum_slippage,
        params=None,
        fee=3000,
    ):
        """Get group transaction for pooling with given asset amounts and maximum slippage.
        The two assets are sent via two :class:`PaymentTxn` / :class:`AssetTransferTxn`. Then, a pool call
        is made from which the LP tokens are issued via inner asset transfer txn. Lastly,
        two redeem residual calls are made to redeem residuals of assets 1 and 2 that
        are not used in the pooling operation. The ratio of the incoming asset amounts
        is compared to the ratio on the smart contract. If it differs (up or down) by more
        than the max_slippage percent, the transaction fails.

        :param sender: sender
        :type sender: str
        :param asset1_amount: asset amount for the first asset
        :type asset1_amount: int
        :param asset2_amount: asset amount for the second asset
        :type asset2_amount: int
        :param maximum_slippage: maximum slippage percent (scaled by 1000000) allowed
        :type maximum_slippage: int
        :return: group transaction for pooling with given asset amounts and maximum slippage
        :rtype: :class:`TransactionGroup`
        """
        if params is None:
            params = get_default_params(self.algod)

        # send asset 1
        txn0 = get_payment_txn(
            sender, params, self.address, asset1_amount, self.asset1.asset_id
        )

        # send asset 2
        txn1 = get_payment_txn(
            sender, params, self.address, asset2_amount, self.asset2.asset_id
        )

        # pool
        params.fee = fee
        txn2 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[
                bytes(POOL_STRINGS.pool, "utf-8"),
                int_to_bytes(maximum_slippage),
            ],
            foreign_apps=[self.manager_application_id],
            foreign_assets=[self.lp_asset_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        # redeem asset 1 residual
        params.fee = 1000
        txn3 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[bytes(POOL_STRINGS.redeem_pool_asset1_residual, "utf-8")],
            foreign_assets=[self.asset1.asset_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        # redeem asset 2 residual
        txn4 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[bytes(POOL_STRINGS.redeem_pool_asset2_residual, "utf-8")],
            foreign_assets=[self.asset2.asset_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        return TransactionGroup([txn0, txn1, txn2, txn3, txn4])

    def get_burn_txns(self, sender, burn_amount, params=None):
        """Get group transaction for burn with given burn amount. The LP token
        is transferred via :class:`AssetTransferTxn`. Then, two burn calls are made,
        one for each asset.

        :param sender: sender
        :type sender: str
        :param burn_amount: lp asset amount to burn
        :type burn_amount: int
        :return: group transaction for burn with given burn amount
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # send lp token
        txn0 = get_payment_txn(
            sender, params, self.address, burn_amount, self.lp_asset_id
        )

        # burn asset 1 out
        params.fee = 2000
        txn1 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[bytes(POOL_STRINGS.burn_asset1_out, "utf-8")],
            foreign_assets=[self.asset1.asset_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        # burn asset 2 out
        txn2 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[bytes(POOL_STRINGS.burn_asset2_out, "utf-8")],
            foreign_assets=[self.asset2.asset_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        return TransactionGroup([txn0, txn1, txn2])

    def get_swap_exact_for_txns(
        self,
        sender,
        swap_in_asset,
        swap_in_amount,
        min_amount_to_receive,
        params=None,
        fee=2000,
    ):
        """Get group transaction for swap exact for transaction. An exact amount of the asset
        to be swapped is sent via a :class:`PaymentTxn` or :class:`AssetTransferTxn`.
        Then, a swap exact for call is made from which the output asset is sent via inner transaction.
        If the output asset amount exceeds the min_amount_to_receive, the transaction succeeds.

        :param sender: sender
        :type sender: str
        :param swap_in_asset: asset to swap
        :type swap_in_asset: :class:`Asset`
        :param swap_in_amount: asset amount of incoming asset
        :type swap_in_amount: int
        :param min_amount_to_receive: minimum amount of outgoing asset to receive, assert failure if not
        :type min_amount_to_receive: int
        :return: group transaction for swap exact for transaction
        :rtype: :class:`TransactionGroup`
        """
        if params is None:
            params = get_default_params(self.algod)

        # send swap in asset
        txn0 = get_payment_txn(
            sender, params, self.address, swap_in_amount, swap_in_asset.asset_id
        )

        # swap exact for
        params.fee = fee
        foreign_assets = (
            [self.asset2.asset_id]
            if swap_in_asset.asset_id == self.asset1.asset_id
            else ([self.asset1.asset_id] if self.asset1.asset_id != 1 else [])
        )
        txn1 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[
                bytes(POOL_STRINGS.swap_exact_for, "utf-8"),
                int_to_bytes(min_amount_to_receive),
            ],
            foreign_apps=[self.manager_application_id],
            foreign_assets=foreign_assets,
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        return TransactionGroup([txn0, txn1])

    def get_swap_for_exact_txns(
        self,
        sender,
        swap_in_asset,
        swap_in_amount,
        amount_to_receive,
        params=None,
        fee=2000,
    ):
        """Get group transaction for swap for exact transaction. An amount of the asset to be
        swapped is sent via a :class:`PaymentTxn` or :class:`AssetTransferTxn`. Then, swap for exact
        call is made to swap for an exact amount of the output asset. If a sufficient amount
        of the incoming asset has been sent, the transaction succeeds. If it succeeds, a
        residual amount of the incoming asset is redeemed by the user in the next call.

        :param sender: sender
        :type sender: str
        :param swap_in_asset: asset to swap
        :type swap_in_asset: :class:`Asset`
        :param swap_in_amount: asset amount of incoming asset
        :type swap_in_amount: int
        :param amount_to_receive: exact amount to receive of outgoing asset, assert fail if not possible
        :type amount_to_receive: int
        :return: group transaction for swap for exact transaction
        :rtype: :class:`TransactionGroup`
        """
        if params is None:
            params = get_default_params(self.algod)

        # send swap in asset
        txn0 = get_payment_txn(
            sender, params, self.address, swap_in_amount, swap_in_asset.asset_id
        )

        # swap for exact
        params.fee = fee
        foreign_assets = (
            [self.asset2.asset_id]
            if swap_in_asset.asset_id == self.asset1.asset_id
            else ([self.asset1.asset_id] if self.asset1.asset_id != 1 else [])
        )
        txn1 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[
                bytes(POOL_STRINGS.swap_for_exact, "utf-8"),
                int_to_bytes(amount_to_receive),
            ],
            foreign_apps=[self.manager_application_id],
            foreign_assets=foreign_assets,
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        # redeem unused swap in asset
        params.fee = 2000
        txn2 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[bytes(POOL_STRINGS.redeem_swap_residual, "utf-8")],
            foreign_apps=[self.manager_application_id],
            foreign_assets=[swap_in_asset.asset_id],
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        return TransactionGroup([txn0, txn1, txn2])

    def get_flash_loan_txns(
        self,
        sender,
        flash_loan_asset,
        flash_loan_amount,
        group_transaction,
        params=None,
    ):
        """Get group transaction for swap exact for transaction

        :param sender: sender
        :type sender: str
        :param flash_loan_asset: asset to borrow in flash loan
        :type flash_loan_asset: :class:`Asset`
        :param flash_loan_amount: asset amount to borrow
        :type flash_loan_amount: int
        :param group_transaction: a group transaction to "sandwich" between flash loan transaction
        :type group_transaction: :class:`TransactionGroup`
        :return: group transaction for flash loan transaction composed with group transaction
        :rtype: :class:`TransactionGroup`
        """
        if params is None:
            params = get_default_params(self.algod)

        # flash loan txn
        params.fee = 2000
        foreign_assets = (
            [self.asset2.asset_id]
            if flash_loan_asset.asset_id == self.asset2.asset_id
            else ([self.asset1.asset_id] if self.asset1.asset_id != 1 else [])
        )
        txn0 = ApplicationNoOpTxn(
            sender=sender,
            sp=params,
            index=self.application_id,
            app_args=[
                bytes(POOL_STRINGS.flash_loan, "utf-8"),
                int_to_bytes(flash_loan_asset.asset_id),
                int_to_bytes(flash_loan_amount),
            ],
            foreign_apps=[self.manager_application_id],
            foreign_assets=foreign_assets,
            note=int(time.time() * 1000 * 1000).to_bytes(8, "big"),
        )

        # repayment txn
        params.fee = 1000
        flash_loan_fee = (
            flash_loan_amount * self.flash_loan_fee
        ) // PARAMETER_SCALE_FACTOR + int(1)
        repay_amount = flash_loan_amount + flash_loan_fee
        txn1 = get_payment_txn(
            sender, params, self.address, repay_amount, flash_loan_asset.asset_id
        )

        # set group to None
        transactions = [txn0] + group_transaction.transactions + [txn1]
        for i in range(len(transactions)):
            transactions[i].group = None

        return TransactionGroup([txn0] + group_transaction.transactions + [txn1])

    @property
    def amplification_factor(self):
        if self.t < self.future_amplification_factor_time:
            return int(
                self.initial_amplification_factor
                + (self.future_amplification_factor - self.initial_amplification_factor)
                * (self.t - self.initial_amplification_factor_time)
                // (
                    self.future_amplification_factor_time
                    - self.initial_amplification_factor_time
                )
            )

        return self.future_amplification_factor

    @property
    def target_ratio(self):
        if self.t < self.target_ratio_adjustment_end_time:
            return (
                self.initial_target_asset1_to_asset2_ratio
                + (self.goal_target_asset1_to_asset2_ratio
                   - self.initial_target_asset1_to_asset2_ratio)
                * (self.t - self.target_ratio_adjustment_start_time)
                / (self.target_ratio_adjustment_end_time
                   - self.target_ratio_adjustment_start_time)
            )

        return self.current_target_asset1_to_asset2_ratio

    def scale_asset1(self, asset_amount):
        if (self.pool_type == PoolType.NANOSWAP_LENDING_POOL):
            return int(asset_amount * self.target_ratio / FIXED_12_SCALE_FACTOR)
        else:
            return asset_amount

    def unscale_asset1(self, asset_amount):
        if (self.pool_type == PoolType.NANOSWAP_LENDING_POOL):
            return int(asset_amount * FIXED_12_SCALE_FACTOR / self.target_ratio)
        else:
            return asset_amount

    def get_empty_pool_quote(self, asset1_pooled_amount, asset2_pooled_amount):
        """Get pool quote for an empty pool

        :param asset1_pooled_amount: asset 1 pooled amount
        :type asset1_pooled_amount: int
        :param asset2_pooled_amount: asset 2 pooled amount
        :type asset2_pooled_amount: int
        :return: pool quote for an empty pool
        :rtype: :class:`BalanceDelta`
        """

        if (self.pool_type == PoolType.NANOSWAP) or (
            self.pool_type == PoolType.NANOSWAP_LENDING_POOL
        ):
            lps_issued, num_iter = get_D(
                [self.scale_asset1(asset1_pooled_amount), asset2_pooled_amount],
                self.amplification_factor
            )
        else:
            num_iter = 0
            if asset1_pooled_amount * asset2_pooled_amount > 2**64 - 1:
                lps_issued = int((asset1_pooled_amount) ** (0.5)) * int(
                    (asset2_pooled_amount) ** (0.5)
                )
            else:
                lps_issued = int((asset1_pooled_amount * asset2_pooled_amount) ** (0.5))

        return BalanceDelta(
            self,
            -1 * asset1_pooled_amount,
            -1 * asset2_pooled_amount,
            lps_issued,
            num_iter,
        )

    def get_pool_quote(self, asset_id, asset_amount):
        """Get full pool quote for a given asset id and amount

        :param asset_id: asset id of the asset to pool
        :type asset_id: int
        :param asset_amount: asset amount of the asset to pool
        :type asset_amount: int
        :return: pool quote for a non-empty pool
        :rtype: :class:`BalanceDelta`
        """

        if self.lp_circulation == 0:
            raise Exception("Error: pool is empty")

        if asset_id == self.asset1.asset_id:
            asset1_pooled_amount = asset_amount
            asset2_pooled_amount = int(
                asset1_pooled_amount * self.asset2_balance // self.asset1_balance
            )
        else:
            asset2_pooled_amount = asset_amount
            asset1_pooled_amount = int(
                asset2_pooled_amount * self.asset1_balance // self.asset2_balance
            )

        if (self.pool_type == PoolType.NANOSWAP) or (
            self.pool_type == PoolType.NANOSWAP_LENDING_POOL
        ):
            D0, num_iter_D0 = get_D(
                [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                self.amplification_factor
            )
            D1, num_iter_D1 = get_D(
                [
                    self.scale_asset1(asset1_balance + asset1_pooled_amount),
                    self.asset2_balance + asset2_pooled_amount,
                ],
                self.amplification_factor,
            )
            lps_issued = int(self.lp_circulation * (D1 - D0) // D0)
            num_iter = num_iter_D0 + num_iter_D1
        else:
            lps_issued = int(
                asset1_pooled_amount * self.lp_circulation // self.asset1_balance
            )
            num_iter = 0

        return BalanceDelta(
            self,
            -1 * asset1_pooled_amount,
            -1 * asset2_pooled_amount,
            lps_issued,
            num_iter,
        )

    def get_burn_quote(self, lp_amount):
        """Get burn quote for a given amount of lps to burn

        :param lp_amount: lp amount to burn
        :type lp_amount: int
        :return: burn quote for a given amount of lps to burn
        :rtype: :class:`BalanceDelta`
        """

        if self.lp_circulation == 0:
            raise Exception("Error: pool is empty")

        if self.lp_circulation < lp_amount:
            raise Exception("Error: cannot burn more lp tokens than are in circulation")

        asset1_amount = int(lp_amount * self.asset1_balance // self.lp_circulation)
        asset2_amount = int(lp_amount * self.asset2_balance // self.lp_circulation)

        return BalanceDelta(self, asset1_amount, asset2_amount, -1 * lp_amount)

    def get_swap_exact_for_quote(self, swap_in_asset_id, swap_in_amount):
        """Get swap exact for quote for a given asset id and swap amount

        :param swap_in_asset_id: id of incoming asset to swap
        :type swap_in_asset_id: int
        :param swap_in_amount: amount of incoming asset to swap
        :type swap_in_amount: int
        :return: swap exact for quote for a given asset id and swap amount
        :rtype: :class:`BalanceDelta`
        """

        if self.lp_circulation == 0:
            raise Exception("Error: pool is empty")

        swap_in_amount_less_fees = swap_in_amount - int(
            math.ceil(swap_in_amount * self.swap_fee)
        )

        if swap_in_asset_id == self.asset1.asset_id:
            if (self.pool_type == PoolType.NANOSWAP) or (
                self.pool_type == PoolType.NANOSWAP_LENDING_POOL
            ):
                D, num_iter_D = get_D(
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    self.amplification_factor,
                )
                y, num_iter_y = get_y(
                    0,
                    1,
                    self.scale_asset1(self.asset1_balance + swap_in_amount_less_fees),
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    D,
                    self.amplification_factor,
                )
                swap_out_amount = self.asset2_balance - y
                num_iter = num_iter_D + num_iter_y
            else:
                swap_out_amount = int(
                    (self.asset2_balance * swap_in_amount_less_fees)
                    // (self.asset1_balance + swap_in_amount_less_fees)
                )
                num_iter = 0
            return BalanceDelta(self, -1 * swap_in_amount, swap_out_amount, 0, num_iter)
        else:
            if (self.pool_type == PoolType.NANOSWAP) or (
                self.pool_type == PoolType.NANOSWAP_LENDING_POOL
            ):
                D, num_iter_D = get_D(
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    self.amplification_factor,
                )
                y, num_iter_y = get_y(
                    1,
                    0,
                    self.asset2_balance + swap_in_amount_less_fees,
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    D,
                    self.amplification_factor,
                )
                swap_out_amount = self.asset1_balance - self.unscale_asset1(y)
                num_iter = num_iter_D + num_iter_y
            else:
                swap_out_amount = int(
                    (self.asset1_balance * swap_in_amount_less_fees)
                    // (self.asset2_balance + swap_in_amount_less_fees)
                )
                num_iter = 0
            return BalanceDelta(self, swap_out_amount, -1 * swap_in_amount, 0, num_iter)

    def get_swap_for_exact_quote(self, swap_out_asset_id, swap_out_amount):
        """Get swap for exact quote for a given asset id and swap amount

        :param swap_out_asset_id: id of outgoing asset
        :type swap_out_asset_id: int
        :param swap_out_amount: amount of outgoing asset
        :type swap_out_amount: int
        :return: swap for exact quote for a given outgoing asset id and amount
        :rtype: :class:`BalanceDelta`
        """

        if self.lp_circulation == 0:
            raise Exception("Error: pool is empty")

        if swap_out_asset_id == self.asset1.asset_id:
            if (self.pool_type == PoolType.NANOSWAP) or (
                self.pool_type == PoolType.NANOSWAP_LENDING_POOL
            ):
                D, num_iter_D = get_D(
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    self.amplification_factor,
                )
                y, num_iter_y = get_y(
                    1,
                    0,
                    self.scale_asset1(self.asset1_balance - swap_out_amount),
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    D,
                    self.amplification_factor,
                )
                swap_in_amount_less_fees = y - self.asset2_balance
                num_iter = num_iter_D + num_iter_y
            else:
                swap_in_amount_less_fees = (
                    int(
                        (self.asset2_balance * swap_out_amount)
                        // (self.asset1_balance - swap_out_amount)
                    )
                    - 1
                )
                num_iter = 0
        else:
            if (self.pool_type == PoolType.NANOSWAP) or (
                self.pool_type == PoolType.NANOSWAP_LENDING_POOL
            ):
                D, num_iter_D = get_D(
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    self.amplification_factor,
                )
                y, num_iter_y = get_y(
                    0,
                    1,
                    self.asset2_balance - swap_out_amount,
                    [self.scale_asset1(self.asset1_balance), self.asset2_balance],
                    D,
                    self.amplification_factor,
                )
                swap_in_amount_less_fees = self.unscale_asset1(y) - self.asset1_balance
                num_iter = num_iter_D + num_iter_y
            else:
                swap_in_amount_less_fees = (
                    int(
                        (self.asset1_balance * swap_out_amount)
                        // (self.asset2_balance - swap_out_amount)
                    )
                    - 1
                )
                num_iter = 0

        swap_in_amount = math.ceil(swap_in_amount_less_fees // (1 - self.swap_fee))

        if swap_out_asset_id == self.asset1.asset_id:
            return BalanceDelta(self, swap_out_amount, -1 * swap_in_amount, 0, num_iter)
        else:
            return BalanceDelta(self, -1 * swap_in_amount, swap_out_amount, 0, num_iter)
