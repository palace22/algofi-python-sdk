# IMPORTS

# external
from typing import List
from base64 import b64encode, b64decode
from algosdk.encoding import encode_address

# global
from ...state_utils import get_local_state_at_app, get_local_states

# local
from .manager import Manager
from .manager_config import MANAGER_CONFIGS
from .market import Market
from .lending_user import LendingUser
from .market_config import MARKET_CONFIGS
from .lending_config import MANAGER_STRINGS

# INTERFACE


class LendingClient:
    def __init__(self, algofi_client):
        """Constructor for the client used to interact with algofi lending protocol

        :param algofi_client: Client for the algofi protocols
        :type algofi_client: :class:`AlgofiClient`
        """

        self.algofi_client = algofi_client
        self.algod = algofi_client.algod
        self.indexer = algofi_client.indexer
        self.historical_indexer = algofi_client.historical_indexer
        self.network = self.algofi_client.network
        self.manager_config = MANAGER_CONFIGS[self.network]
        self.market_configs = MARKET_CONFIGS[self.network]

        self.manager = Manager(self, self.manager_config)
        self.markets = {}
        for market_config in self.market_configs:
            self.markets[market_config.app_id] = Market(self, market_config)

    def load_state(self, block=None):
        """Function to update the state of the lending client markets"""
        for market_app_id in self.markets:
            self.markets[market_app_id].load_state(block=block)

    def get_user(self, user_address, storage_address=None):
        """Gets an algofi lending v2 user given an address.

        :param user_address: the address of the user we are interested in.
        :type user_address: str
        :param storage_address: a storage address of the user wallet
        :type storage_address: str, optional
        :return: an algofi lending v2 user.
        :rtype: :class:`LendingUser`
        """

        if storage_address:
            return LendingUser(self, None, storage_address=storage_address)
        else:
            return LendingUser(self, user_address)


    def get_storage_accounts(self, verbose=False):
        """Fetches the list of user storage accounts on the lending protocol from the blockchain

        :param verbose: return account address with full account data (e.g. created apps / assets, local state, balances)
        :type verbose: bool, optional
        :return: list of storage account address strings
        :rtype: list
        """

        next_page = ""
        accounts = []
        while next_page is not None:
            account_data = self.indexer.accounts(
                limit=1000,
                next_page=next_page,
                application_id=self.manager.app_id,
                exclude="assets,created-apps,created-assets",
            )
            accounts_filtered = []
            for account in account_data["accounts"]:
                user_local_state = account.get("apps-local-state", [])
                for app_local_state in user_local_state:
                    if app_local_state["id"] == self.manager.app_id:
                        fields = app_local_state.get("key-value", [])
                        for field in fields:
                            key = field.get("key", None)
                            if key == b64encode(
                                bytes(MANAGER_STRINGS.user_account, "utf-8")
                            ).decode("utf-8"):
                                accounts_filtered.append(account)
            accounts.extend(
                [
                    (account if verbose else account["address"])
                    for account in accounts_filtered
                ]
            )
            if "next-token" in account_data:
                next_page = account_data["next-token"]
            else:
                next_page = None
        return accounts

    def get_user_account(self, storage_account):
        manager_state = get_local_state_at_app(
            self.indexer, storage_account, self.manager.app_id
        )
        if manager_state:
            return encode_address(
                b64decode(manager_state[MANAGER_STRINGS.user_account])
            )
        return ""
    
    def get_storage_account(self, user_account):
        manager_state = get_local_state_at_app(
            self.indexer, user_account, self.manager.app_id
        )
        if manager_state:
            return encode_address(
                b64decode(manager_state[MANAGER_STRINGS.storage_account])
            )
        return ""