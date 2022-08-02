# IMPORTS

# external

# local
from .algofi_user import AlgofiUser
from .asset_config import ASSET_CONFIGS

# lending
from .lending.v2.lending_client import LendingClient
from .staking.v2.staking_client import StakingClient

class AlgofiClient:
    def __init__(self, network, algod, indexer):
        """A client for the algofi protocol

        :param network: a network configuration key
        :type network: :class:`Network`
        :param algod: Algod client
        :type algod: :class:`AlgodClient`
        :param indexer: Algorand indexer client
        :type indexer: :class:`IndexerClient`
        """
        self.network = network
        self.algod = algod
        self.indexer = indexer
        
        # assets
        self.assets = ASSET_CONFIGS[self.network]
        
        # lending
        self.lending = LendingClient(self)

        # staking
        self.staking = StakingClient(self)

    def get_user(self, address):
        """Creates an :class:`AlgofiUser` object for specific address

        :param address: string address of the user primary wallet
        :type address: str
        :return: Python representation of the algofi user
        :rtype: :class:`AlgofiUser`
        """
        return AlgofiUser(self, address)