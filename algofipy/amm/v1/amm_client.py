# IMPORTS

# external
from algosdk import logic
from .amm_config import (
    Network,
    POOL_STRINGS,
    MANAGER_STRINGS,
    MAINNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID,
    TESTNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID,
    MAINNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID,
    TESTNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID,
    NANOSWAP_LENDING_POOLS_ASSET_PAIR_TO_APP_ID,
    CONSTANT_PRODUCT_LENDING_POOLS_ASSET_PAIR_TO_APP_ID,
    get_pool_type,
    PoolType,
)
from algofipy.state_utils import get_accounts_opted_into_app, format_state
from .logic_sig_generator import generate_logic_sig
from .pool import Pool
from .asset import Asset

# local

# INTERFACE


class AMMClient:
    def __init__(self, algofi_client):
        """Constructor method for :class:`Client`

        :param algofi_client: a :class:`AlgofiClient` object for interacting with the network
        :type algofi_client: :class:`AlgofiClient`
        :param user_address: user address
        :type user_address: str, optional
        """

        # clients info
        self.algofi_client = algofi_client
        self.algod = algofi_client.algod
        self.indexer = algofi_client.indexer
        self.historical_indexer = algofi_client.historical_indexer
        self.network = self.algofi_client.network
        self.manager_application_id = (
            MAINNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID
            if self.network == Network.MAINNET
            else TESTNET_CONSTANT_PRODUCT_POOLS_MANAGER_APP_ID
        )
        self.nanoswap_pool_app_ids = (
            MAINNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID
            if self.network == Network.MAINNET
            else TESTNET_NANOSWAP_POOLS_ASSET_PAIR_TO_APP_ID
        )

    def get_pool(self, pool_type, asset1_id, asset2_id):
        """Returns a :class:`Pool` object for given assets and pool_type

        :param pool_type: a :class:`PoolType` object for the type of pool (e.g. 30bp, 100bp fee)
        :type pool_type: :class:`PoolType`
        :param asset1_id: asset 1 id
        :type asset1_id: int
        :param asset2_id: asset 2 id
        :type asset2_id: int
        :return: a :class:`Pool` object for given assets and pool_type
        :rtype: :class:`Pool`
        """

        if asset1_id == asset2_id:
            raise Exception("Invalid assets. must be different")

        asset1 = Asset(self, asset1_id)
        asset2 = Asset(self, asset2_id)

        if asset1_id < asset2_id:
            pool = Pool(self.algofi_client.amm, pool_type, asset1, asset2)
        else:
            pool = Pool(self.algofi_client.amm, pool_type, asset2, asset1)

        return pool

    def get_asset(self, asset_id):
        """Returns an :class:`Asset` object representing the asset with given asset id

        :param asset_id: asset id
        :type asset_id: int
        :return: :class:`Asset` object representing the asset with given asset id
        :rtype: :class:`Asset`
        """

        asset = Asset(self, asset_id)
        return asset

    def get_constant_product_pools(self):
        """Returns a dict of valid constant product pools with relevant data

        :return: dict mapping pool app id -> :class:`Pool`
        :rtype: dict
        """

        def validate_pool(account_data):
            # process account data
            account_local_state = account_data.get("apps-local-state", [])
            if len(account_local_state) > 1:
                return None
            manager_app_local_state = format_state(account_local_state[0]["key-value"])

            # get pool metadata from manager local state
            asset1_id = manager_app_local_state.get(POOL_STRINGS.asset1_id, "")
            asset2_id = manager_app_local_state.get(POOL_STRINGS.asset2_id, "")
            validator_index = manager_app_local_state.get(
                POOL_STRINGS.validator_index, ""
            )
            pool_app_id = manager_app_local_state.get(POOL_STRINGS.pool, "")
            pool_type = get_pool_type(self.network, validator_index)

            # check logic sig equality to ensure no duplicate pools
            logic_sig_bytes = generate_logic_sig(
                asset1_id, asset2_id, self.manager_application_id, validator_index
            )
            address = logic.address(logic_sig_bytes)
            if address != account_data.get("address", None):
                return None

            try:
                pool = self.get_pool(pool_type, asset1_id, asset2_id)
            except:
                # asset1, asset2, or both have been destroyed
                return None

            return (pool_app_id, pool)

        accounts = get_accounts_opted_into_app(
            self.indexer, self.manager_application_id
        )
        valid_pool_data = dict(
            list(
                filter(
                    lambda x: x != None,
                    [validate_pool(account) for account in accounts],
                )
            )
        )

        return valid_pool_data

    def get_nanoswap_pools(self):
        """Returns a dict of valid nanoswap pools with relevant data

        :return: dict mapping nanoswap pool app id -> :class:`Pool`
        :rtype: dict
        """

        return dict(
            [
                (
                    pool_app_id,
                    self.get_pool(PoolType.NANOSWAP, asset1_id, asset2_id),
                )
                for (
                    (asset1_id, asset2_id),
                    pool_app_id,
                ) in self.nanoswap_pool_app_ids.items()
            ]
        )

    def get_constant_product_lending_pools(self):
        """Returns a dict of valid constant product lending pools with relevant data

        :return: dict mapping constant product lending pool app id -> :class:`Pool`
        :rtype: dict
        """

        if self.network == Network.TESTNET:
            raise Exception("Lending Pool is not on testnet")

        return dict(
            [
                (
                    pool_app_id,
                    self.get_pool(PoolType.CONSTANT_PRODUCT_25BP_FEE_LENDING_POOL, asset1_id, asset2_id),
                )
                for (
                    (asset1_id, asset2_id),
                    pool_app_id,
                ) in CONSTANT_PRODUCT_LENDING_POOLS_ASSET_PAIR_TO_APP_ID.items()
            ]
        )

    def get_nanoswap_lending_pools(self):
        """Returns a dict of valid nanoswap lending pools with relevant data

        :return: dict mapping nanoswap lending pool app id -> :class:`Pool`
        :rtype: dict
        """

        if self.network == Network.TESTNET:
            raise Exception("Lending Pool is not on testnet")

        return dict(
            [
                (
                    pool_app_id,
                    self.get_pool(PoolType.NANOSWAP_LENDING_POOL, asset1_id, asset2_id),
                )
                for (
                    (asset1_id, asset2_id),
                    pool_app_id,
                ) in NANOSWAP_LENDING_POOLS_ASSET_PAIR_TO_APP_ID.items()
            ]
        )
