# IMPORTS

# global
from algofipy.globals import Network

# local
from .lending_config import MarketType

# INTERFACE

class MarketConfig:
    def __init__(self, app_id, underlying_asset_id, b_asset_id, market_type):
        self.app_id = app_id
        self.underlying_asset_id = underlying_asset_id
        self.b_asset_id = b_asset_id
        self.market_type = market_type

MARKET_CONFIGS = {
  Network.MAINNET : [
    MarketConfig(818179346, 1, 818179690, MarketType.STANDARD), # ALGO
    MarketConfig(818182048, 31566704, 818182311, MarketType.STANDARD), # USDC
    MarketConfig(818183964, 386192725, 818184214, MarketType.STANDARD), # goBTC
    MarketConfig(818188286, 386195940, 818188553, MarketType.STANDARD), # goETH
    MarketConfig(818190205, 312769, 818190568, MarketType.STANDARD), # USDT
  ]
}