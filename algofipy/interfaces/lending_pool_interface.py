# IMPORTS

# external
from algosdk import logic
from algosdk.future.transaction import ApplicationNoOpTxn, LogicSigAccount

# local
from .lending_pool_interface_config import LENDING_POOL_INTERFACE_STRINGS

# global
from algofipy.globals import Network
from algofipy.amm.v1.pool import Pool
from algofipy.amm.v1.balance_delta import BalanceDelta
from algofipy.amm.v1.asset import Asset
from algofipy.amm.v1.amm_config import PoolType
from algofipy.transaction_utils import get_payment_txn, get_default_params, TransactionGroup
from algofipy.utils import int_to_bytes

# INTERFACE

# constants

PERMISSIONLESS_SENDER_LOGIC_SIG = LogicSigAccount(
    bytes([6, 49, 16, 129, 6, 18, 68, 49, 25, 129, 0, 18, 68, 49, 9, 50, 3, 18, 68, 49, 32, 50, 3, 18, 68, 129, 1, 67])
)

class LendingPoolInterface:

    def __init__(self, algofi_client, config):
        self.algofi_client = algofi_client
        self.algod = self.algofi_client.algod
        self.app_id = config.app_id
        self.market1_app_id = config.market1_app_id
        self.market2_app_id = config.market2_app_id
        self.lp_market_app_id = config.lp_market_app_id
        self.pool_app_id = config.pool_app_id
        self.op_farm_app_id = config.op_farm_app_id

        self.address = logic.get_application_address(self.app_id)

        # load markets, pool, and lp market
        self.market1 = algofi_client.lending.markets[self.market1_app_id]
        self.market2 = algofi_client.lending.markets[self.market2_app_id]
        self.lp_market = algofi_client.lending.markets[self.lp_market_app_id]
        self.pool = Pool(
            algofi_client.amm,
            config.pool_type,
            Asset(self.algofi_client.amm, self.market1.b_asset_id),
            Asset(self.algofi_client.amm, self.market2.b_asset_id)
        )
    
    def load_state(self):
        # refresh markets + pool
        self.market1.load_state()
        self.market2.load_state()
        self.lp_market.load_state()
        self.pool.refresh_state()

    def get_pool_quote(self, asset_id, amount):

        asset1_pooled_amount = 0
        b_asset1_pooled_amount = 0
        asset2_pooled_amount = 0
        b_asset2_pooled_amount = 0
        lps_issued = 0
        num_iter = 0

        if asset_id == self.market1.underlying_asset_id:
            asset1_pooled_amount = amount
            b_asset1_pooled_amount = self.market1.underlying_to_b_asset(amount)
            pool_quote = self.pool.get_pool_quote(self.market1.b_asset_id, b_asset1_pooled_amount)
            b_asset2_pooled_amount = -1 * pool_quote.asset2_delta
            asset2_pooled_amount = self.market2.b_asset_to_asset_amount(b_asset2_pooled_amount).underlying
            lps_issued = pool_quote.lp_delta
            num_iter = pool_quote.num_iter
        else:
            asset2_pooled_amount = amount
            b_asset2_pooled_amount = self.market2.underlying_to_b_asset(amount)
            pool_quote = self.pool.get_pool_quote(self.market2.b_asset_id, b_asset2_pooled_amount)
            b_asset1_pooled_amount = -1 * pool_quote.asset1_delta
            asset1_pooled_amount = self.market1.b_asset_to_asset_amount(b_asset1_pooled_amount).underlying
            lps_issued = pool_quote.lp_delta
            num_iter = pool_quote.num_iter

        return BalanceDelta(self.pool, -1 * asset1_pooled_amount, -1 * asset2_pooled_amount, lps_issued, num_iter)        

    def get_pool_txns(self, user, quote, maximum_slippage, add_to_user_collateral=False, params=None):

        if params is None:
            params = get_default_params(self.algod)

        additional_permisionless_fee = 27000 + quote.num_iter * 1000 + (3000 if add_to_user_collateral else 1000)

        # send asset 1
        txn0 = get_payment_txn(user.address, params, self.address, -1* quote.asset1_delta, self.market1.underlying_asset_id)

        # send asset 2
        txn1 = get_payment_txn(user.address, params, self.address, -1 * quote.asset2_delta, self.market2.underlying_asset_id)

        # pool step 1
        params.fee = 1000 + additional_permisionless_fee
        txn2 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.app_id,
            app_args=[
                bytes(LENDING_POOL_INTERFACE_STRINGS.pool_step_1, "utf-8"),
                int_to_bytes(quote.num_iter)
            ],
            foreign_apps=[self.op_farm_app_id]
        )

        # pool step 2
        params.fee = 0
        txn3 = ApplicationNoOpTxn(
            sender=PERMISSIONLESS_SENDER_LOGIC_SIG.address(),
            sp=params,
            index=self.app_id,
            app_args=[
                bytes(LENDING_POOL_INTERFACE_STRINGS.pool_step_2, "utf-8"),
            ],
            accounts=[self.market1.address],
            foreign_apps=[self.market1.app_id, self.market1.manager_app_id],
            foreign_assets=[self.market1.underlying_asset_id, self.market1.b_asset_id]
        )

        # pool step 3
        params.fee = 0
        txn4 = ApplicationNoOpTxn(
            sender=PERMISSIONLESS_SENDER_LOGIC_SIG.address(),
            sp=params,
            index=self.app_id,
            app_args=[
                bytes(LENDING_POOL_INTERFACE_STRINGS.pool_step_3, "utf-8"),
            ],
            accounts=[self.market2.address],
            foreign_apps=[self.market2.app_id, self.market2.manager_app_id],
            foreign_assets=[self.market2.underlying_asset_id, self.market2.b_asset_id]
        )

        # pool step 4
        params.fee = 0
        txn5 = ApplicationNoOpTxn(
            sender=PERMISSIONLESS_SENDER_LOGIC_SIG.address(),
            sp=params,
            index=self.app_id,
            app_args=[
                bytes(LENDING_POOL_INTERFACE_STRINGS.pool_step_4, "utf-8"),
                int_to_bytes(maximum_slippage)
            ],
            accounts=[self.pool.address],
            foreign_apps=[self.pool.application_id, self.pool.manager_application_id],
            foreign_assets=[self.pool.asset1.asset_id, self.pool.asset2.asset_id, self.pool.lp_asset_id]
        )

        # pool step 5
        params.fee = 0
        txn6 = ApplicationNoOpTxn(
            sender=PERMISSIONLESS_SENDER_LOGIC_SIG.address(),
            sp=params,
            index=self.app_id,
            app_args=[
                bytes(LENDING_POOL_INTERFACE_STRINGS.pool_step_5, "utf-8"),
                int_to_bytes(1) if add_to_user_collateral else int_to_bytes(0)
            ],
            accounts=[user.address, user.lending.storage_address, self.lp_market.address] if user.lending.opted_in_to_manager else [user.address, self.lp_market.address],
            foreign_apps=[self.lp_market.app_id, self.lp_market.manager_app_id],
            foreign_assets=[self.lp_market.underlying_asset_id]
        )

        # pool step 6
        params.fee = 0
        txn7 = ApplicationNoOpTxn(
            sender=PERMISSIONLESS_SENDER_LOGIC_SIG.address(),
            sp=params,
            index=self.app_id,
            app_args=[
                bytes(LENDING_POOL_INTERFACE_STRINGS.pool_step_6, "utf-8")
            ],
            accounts=[user.address, self.market1.address],
            foreign_apps=[self.market1.app_id, self.market1.manager_app_id],
            foreign_assets=[self.market1.underlying_asset_id, self.market1.b_asset_id]
        )

        # pool step 7
        params.fee = 0
        txn8 = ApplicationNoOpTxn(
            sender=PERMISSIONLESS_SENDER_LOGIC_SIG.address(),
            sp=params,
            index=self.app_id,
            app_args=[
                bytes(LENDING_POOL_INTERFACE_STRINGS.pool_step_7, "utf-8")
            ],
            accounts=[user.address, self.market2.address],
            foreign_apps=[self.market2.app_id, self.market2.manager_app_id],
            foreign_assets=[self.market2.underlying_asset_id, self.market2.b_asset_id]
        )

        return TransactionGroup([txn0, txn1, txn2, txn3, txn4, txn5, txn6, txn7, txn8])
        