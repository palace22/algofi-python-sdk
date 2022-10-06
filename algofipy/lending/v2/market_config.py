# IMPORTS

# global
from algofipy.globals import Network

# local
from .lending_config import MarketType

# INTERFACE

class MarketConfig:
    def __init__(self, name, app_id, underlying_asset_id, b_asset_id, market_type):
        """A market config

        :param name: name of market
        :type name: str
        :param app_id: application id
        :type app_id: int
        :param underlying_asset_id: underlying asset id of market
        :type underlying_asset_id: int
        :param b_asset_id: b asset id of market
        :type b_asset_id: int
        :param market_type: market type
        :type market_type: :class:`MarketType`
        """

        self.name = name
        self.app_id = app_id
        self.underlying_asset_id = underlying_asset_id
        self.b_asset_id = b_asset_id
        self.market_type = market_type

MARKET_CONFIGS = {
  Network.MAINNET : [
    MarketConfig("ALGO", 818179346, 1, 818179690, MarketType.STANDARD), # ALGO
    MarketConfig("USDC", 818182048, 31566704, 818182311, MarketType.STANDARD), # USDC
    MarketConfig("goBTC", 818183964, 386192725, 818184214, MarketType.STANDARD), # goBTC
    MarketConfig("goETH", 818188286, 386195940, 818188553, MarketType.STANDARD), # goETH
    MarketConfig("USDT", 818190205, 312769, 818190568, MarketType.STANDARD), # USDT
    MarketConfig("STBL2", 841145020, 841126810, 841157954, MarketType.STBL), # STBL2
    MarketConfig("vALGO", 879935316, 1, 879951266, MarketType.VAULT), # ALGO VAULT
    MarketConfig("STBL2-USDC-LP", 841194726, 841171328, 841462373, MarketType.LP), # STBL2-USDC LP
    MarketConfig("STBL2-ALGO-LP", 856183130, 855717054, 856217307, MarketType.LP), # STBL2-ALGO LP
    MarketConfig("STBL2-goBTC-LP", 870271921, 870151164, 870380101, MarketType.LP), # STBL2-goBTC LP
    MarketConfig("STBL2-goETH-LP", 870275741, 870150187, 870391958, MarketType.LP) # STBL2-goETH LP
  ],
  Network.TESTNET : [
    MarketConfig("ALGO", 104193717, 1, 104193939, MarketType.STANDARD), # ALGO
    MarketConfig("USDC", 104207076, 104194013, 104207173, MarketType.STANDARD), # USDC
    MarketConfig("USDT", 104209685, 104208050, 104222974, MarketType.STANDARD), # USDT
    MarketConfig("goBTC", 104207403, 104207287, 104207503, MarketType.STANDARD), # goBTC
    MarketConfig("goETH", 104207719, 104207533, 104207983, MarketType.STANDARD), # goETH
    MarketConfig("STBL2", 104213311, 104210500, 104217422, MarketType.STBL), # STBL2
    MarketConfig("bUSDC-bSTBL2 LP", 104238373, 104228491, 104238470, MarketType.LP) # bUSDC-bSTBL2 LP
  ]
}