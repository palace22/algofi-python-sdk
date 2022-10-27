# IMPORTS

# external
from typing import List
from base64 import b64encode

# local
from .lending_pool_interface_config import LENDING_POOL_INTERFACE_CONFIGS, LENDING_POOL_INTERFACE_STRINGS
from .lending_pool_interface import LendingPoolInterface

# INTERFACE

class InterfaceClient:
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
        self.lending_pool_configs = LENDING_POOL_INTERFACE_CONFIGS[self.network]
        
        self.lending_pool_interfaces = {}
        self.asset_lending_pool_map = {}
        self.lp_lending_pool_map = {}
        for lending_pool_config in self.lending_pool_configs:
            self.lending_pool_interfaces[lending_pool_config.app_id] = LendingPoolInterface(self.algofi_client, lending_pool_config)
            self.asset_lending_pool_map[(lending_pool_config.asset1_id, lending_pool_config.asset2_id)] = self.lending_pool_interfaces[lending_pool_config.app_id]
            self.lp_lending_pool_map[lending_pool_config.lp_asset_id] = self.lending_pool_interfaces[lending_pool_config.app_id]