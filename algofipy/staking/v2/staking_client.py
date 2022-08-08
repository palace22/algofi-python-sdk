from .staking_config import STAKING_CONFIGS, rewards_manager_app_id
from .staking import Staking
from .staking_user import StakingUser

class StakingClient: 

    def __init__(self, algofi_client):
        self.algofi_client = algofi_client
        self.algod = self.algofi_client.algod
        self.indexer = self.algofi_client.indexer
        self.historical_indexer = self.algofi_client.historical_indexer
        self.network = self.algofi_client.network
        self.historical_indexer = self.algofi_client.historical_indexer
        self.staking_configs = STAKING_CONFIGS[self.network]

        self.staking_contracts = {}
        for staking_config in self.staking_configs:
            self.staking_contracts[staking_config.app_id] = Staking(self, rewards_manager_app_id[self.network], staking_config)
            self.staking_contracts[staking_config.app_id].load_state()