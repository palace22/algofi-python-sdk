# IMPORTS

# external


# local
from .manager_config import MANAGER_CONFIGS
from .manager import Manager
from .market_config import MARKET_CONFIGS
from .market import Market
from .lending_user import LendingUser

# INTERFACE
from ...algofi_client import AlgofiClient


class LendingClient:
    def __init__(self, algofi_client: AlgofiClient):
        self.algofi_client = algofi_client
        self.algod = algofi_client.algod
        self.indexer = algofi_client.indexer
        
        self.manager_config = MANAGER_CONFIGS[self.algofi_client.network]
        self.market_configs = MARKET_CONFIGS[self.algofi_client.network]
        
        self.manager = Manager(self, self.manager_config)
        self.markets = {}
        for market_config in self.market_configs:
            self.markets[market_config.app_id] = Market(self, market_config)
    
    
    def get_storage_accounts(self): # TODO fix this to only return storage accounts
        next_page = ""
        accounts = []
        while next_page is not None:
            account_data = self.indexer.accounts(limit=1000, next_page=next_page, application_id=self.manager.app_id)
            accounts.extend([account["address"] for account in account_data["accounts"]])
            if "next-token" in account_data:
                next_page = account_data["next-token"]
            else:
                next_page = None
        return accounts