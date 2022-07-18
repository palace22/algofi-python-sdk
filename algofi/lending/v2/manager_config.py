# IMPORTS

# INTERFACE
from algofi.globals import Network


class ManagerConfig:
    def __init__(self, app_id):
        self.app_id = app_id

MANAGER_CONFIGS = {
    Network.MAINNET : ManagerConfig(0),
    Network.MAINNET_CLONE : ManagerConfig(753081696),
    Network.TESTNET : ManagerConfig(91633688)
}