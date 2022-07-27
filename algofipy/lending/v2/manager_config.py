# IMPORTS

# INTERFACE
from algofipy.globals import Network


class ManagerConfig:
    def __init__(self, app_id):
        """An object storing lending manager metadata"""
        self.app_id = app_id

MANAGER_CONFIGS = {
    Network.MAINNET : ManagerConfig(818176933),
}