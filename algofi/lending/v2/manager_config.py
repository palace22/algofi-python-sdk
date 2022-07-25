# IMPORTS

# INTERFACE
from algofi.globals import Network


class ManagerConfig:
    def __init__(self, app_id):
        """An object storing lending manager metadata"""
        self.app_id = app_id

MANAGER_CONFIGS = {
    Network.MAINNET : ManagerConfig(0),
    Network.MAINNET_CLONE : ManagerConfig(753081696),
    Network.MAINNET_CLONE2 : ManagerConfig(802875339),
    Network.TESTNET : ManagerConfig(91633688)
}