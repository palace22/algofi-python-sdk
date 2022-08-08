
# IMPORTS

# external
from algosdk import logic
from .amm_config import Network, get_manager_application_id, b64_to_utf_keys, utf_to_b64_keys, POOL_STRINGS, MANAGER_STRINGS
from .logic_sig_generator import generate_logic_sig
from .pool import Pool
from .asset import Asset

# local

# INTERFACE

class AMMClient():

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
        self.network = Network.MAINNET
        self.manager_application_id = get_manager_application_id(self.network, False)

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

        if (asset1_id == asset2_id):
            raise Exception("Invalid assets. must be different")

        asset1 = Asset(self, asset1_id)
        asset2 = Asset(self, asset2_id)

        if (asset1_id < asset2_id):
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

    def get_valid_pool_app_ids(self):
        """Returns a list of valid pool app ids.

        :return: a :class:`Pool` object for given assets and pool_type
        :rtype: :class:`Pool`
        """

        nextpage = ""
        accounts = []
        # get accounts opted in to
        while nextpage is not None:
            account_data = self.indexer.accounts(limit=1000, next_page=nextpage, application_id=self.manager_application_id)
            accounts_interim = account_data.get("accounts", [])
            if accounts_interim:
                accounts.extend(accounts_interim)
            nextpage = account_data.get("next-token", None)
        # filter accounts by logic sig
        pool_app_ids = []
        for account in accounts:
            account_local_state = account.get("apps-local-state", {})
            # number of opted in apps is only 1
            if len(account_local_state) == 1:
                a1, a2, vi, p = None, None, None, None
                account_local_state = account_local_state[0].get("key-value", [])
                for data in account_local_state:
                    key, value = data["key"], data["value"]
                    # key must be in mapping
                    if key not in b64_to_utf_keys:
                        break
                    if key == utf_to_b64_keys[POOL_STRINGS.asset1_id]:
                        a1 = value["uint"]
                    elif key == utf_to_b64_keys[POOL_STRINGS.asset2_id]:
                        a2 = value["uint"]
                    elif key == utf_to_b64_keys[MANAGER_STRINGS.validator_index]:
                        vi = value["uint"]
                    elif key == utf_to_b64_keys[POOL_STRINGS.pool]:
                        p = value["uint"]
                # has data for each field
                if a1 and a2 and p and (vi != None):
                    # compute address
                    logic_sig_bytes = generate_logic_sig(a1, a2, self.manager_application_id, vi)
                    address = logic.address(logic_sig_bytes)
                    # check implied logic sig address matches opted in account address
                    if address == account.get("address", None):
                        pool_app_ids.append(p)

        return pool_app_ids
