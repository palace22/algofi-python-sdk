# IMPORTS

# INTERFACE
from algofipy.globals import Network


class ManagerConfig:
    def __init__(self, app_id):
        """An object storing lending manager metadata

        :param app_id: application id
        :type app_id: int
        """

        self.app_id = app_id


MANAGER_CONFIGS = {
    Network.MAINNET: ManagerConfig(818176933),
    Network.TESTNET: ManagerConfig(104184985),
}
