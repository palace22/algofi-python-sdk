# IMPORTS

# global
from ..globals import Network

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
    MarketConfig(0, 1, 0, MarketType.STANDARD) # ALGO
  ],
  Network.MAINNET_CLONE : [
    MarketConfig(753107352, 1, 753117075, MarketType.STANDARD), # ALGO
    MarketConfig(753108247, 753101315, 753119272, MarketType.STANDARD), # USDC
    MarketConfig(753108576, 753101485, 753119789, MarketType.STANDARD), # USDT
    MarketConfig(753109347, 753101784, 753120193, MarketType.STANDARD), # STBL
    MarketConfig(753110308, 753102180, 753120742, MarketType.STANDARD), # GOBTC
    MarketConfig(753110704, 753102376, 753121086, MarketType.STANDARD), # GOETH
    MarketConfig(753110470, 753103642, 753121416, MarketType.STANDARD), # WBTC
    MarketConfig(753110943, 753103963, 753121726, MarketType.STANDARD), # WETH
    MarketConfig(753111321, 753104158, 753122003, MarketType.STANDARD), # WSOL
    MarketConfig(753111740, 753104718, 753122293, MarketType.STANDARD), # BANK
    MarketConfig(753112308, 1, 753122631, MarketType.STANDARD), # vALGO
  ],
  Network.TESTNET : [
    MarketConfig(91635808, 1, 91638233, MarketType.STANDARD),
    MarketConfig(91636097, 91634316, 91638306, MarketType.STANDARD),
    MarketConfig(91636162, 91634828, 91638392, MarketType.STANDARD),
    MarketConfig(91636638, 91634454, 91638538, MarketType.STANDARD),
    MarketConfig(91636680, 91634487, 91638603, MarketType.STANDARD),
    MarketConfig(91636742, 91634534, 91638687, MarketType.STANDARD),
    MarketConfig(91636787, 91634562, 91638794, MarketType.STANDARD),
    MarketConfig(91636896, 91634691, 91638864, MarketType.STANDARD),
    MarketConfig(91637209, 1, 91639146, MarketType.VAULT),
    MarketConfig(91637110, 91634578, 91638952, MarketType.STBL),
    MarketConfig(91636998, 91634736, 91639074, MarketType.STANDARD),
  ]
}