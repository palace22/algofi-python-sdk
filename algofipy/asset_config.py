# IMPORTS

# global
from algofipy.globals import Network

# INTERFACE

class AssetConfig:
    def __init__(self, name, asset_id, decimals):
        self.name = name
        self.asset_id = asset_id
        self.decimals = decimals

ASSET_CONFIGS = {
    Network.MAINNET : {
        1: AssetConfig("ALGO", 1, 6),
        818179690: AssetConfig("AF-BANK-ALGO-STANDARD", 818179690, 6),
        31566704: AssetConfig("USDC", 818179690, 6),
        818182311: AssetConfig("AF-BANK-USDC-STANDARD", 818182311, 6),
        386192725 : AssetConfig("GOBTC", 386192725, 8),
        818184214: AssetConfig("AF-BANK-GOBTC-STANDARD", 818184214, 6),
        386195940: AssetConfig("GOETH", 386195940, 8),
        818188553: AssetConfig("AF-BANK-GOETH-STANDARD", 818188553, 6),
        312769: AssetConfig("USDT", 312769, 6),
        818190568: AssetConfig("AF-BANK-USDT-STANDARD", 818190568, 6)
    },
    Network.MAINNET_CLONE : {
        1 : AssetConfig("ALGO", 1, 6),
        753117075 : AssetConfig("AF-BANK-ALGO-STANDARD", 753117075, 6),
        753101315 : AssetConfig("USDC", 753101315, 6),
        753119272 : AssetConfig("AF-BANK-USDC-STANDARD", 753119272, 6),
        753101485 : AssetConfig("USDT", 753101485, 6),
        753119789 : AssetConfig("AF-BANK-USDT-STANDARD", 753119789, 6),
        753102180 : AssetConfig("GOBTC", 753102180, 8),
        753120742 : AssetConfig("AF-BANK-GOBTC-STANDARD", 753120742, 6),
        753102376 : AssetConfig("GOETH", 753102376, 8),
        753121086 : AssetConfig("AF-BANK-GOETH-STANDARD", 753121086, 6),
        753103963 : AssetConfig("WETH", 753103963, 6),
        753121726 : AssetConfig("AF-BANK-WETH-STANDARD", 753121726, 6),
        753103642 : AssetConfig("WBTC", 753103642, 6),
        753121416 : AssetConfig("AF-BANK-WBTC-STANDARD", 753121416, 6),
        753104158 : AssetConfig("WSOL", 753104158, 6),
        753122003 : AssetConfig("AF-BANK-WSOL-STANDARD", 753122003, 6),
        753122631 : AssetConfig("AF-BANK-ALGO-VAULT", 753122631, 6),
        753101784 : AssetConfig("STBL", 753101784, 6),
        753120193 : AssetConfig("AF-BANK-STBL-STBL", 753120193, 6),
        753104718 : AssetConfig("BANK", 753104718, 6),
        753122293 : AssetConfig("AF-BANK-BANK-STANDARD", 753122293, 6),
    },
    Network.MAINNET_CLONE2 : {
        1: AssetConfig("ALGO", 1, 6),
        802887010: AssetConfig("AF-BANK-ALGO-STANDARD", 802887010, 6),
        802871797: AssetConfig("USDC", 802871797, 6),
        802887476: AssetConfig("AF-BANK-USDC-STANDARD", 802887476, 6),
        802873705: AssetConfig("goBTC", 802873705, 8),
        802888469: AssetConfig("AF-BANK-GOBTC-STANDARD", 802888469, 6),
        802874445: AssetConfig("goETH", 802874445, 8),
        802888853: AssetConfig("AF-BANK-GOETH-STANDARD", 802888853, 6),
        802872834: AssetConfig("STBL2", 802872834, 6),
        802887973: AssetConfig("AF-BANK-STBL-STBL2", 802887973, 6),
    },
    Network.TESTNET : {
        1 : AssetConfig("ALGO", 1, 6),
        91638233 : AssetConfig("AF-BANK-ALGO-STANDARD", 91638233, 6),
        91634316 : AssetConfig("USDC", 91634316, 6),
        91638306 : AssetConfig("AF-BANK-USDC-STANDARD", 91638306, 6),
        91634828 : AssetConfig("USDT", 91634828, 6),
        91638392 : AssetConfig("AF-BANK-USDT-STANDARD", 91638392, 6),
        91634454 : AssetConfig("GOBTC", 91634454, 8),
        91638538 : AssetConfig("AF-BANK-GOBTC-STANDARD", 91638538, 6),
        91634487 : AssetConfig("GOETH", 91634487, 8),
        91638603 : AssetConfig("AF-BANK-GOETH-STANDARD", 91638603, 6),
        91634534 : AssetConfig("WETH", 91634534, 6),
        91638687 : AssetConfig("AF-BANK-WETH-STANDARD", 91638687, 6),
        91634562 : AssetConfig("WBTC", 91634562, 6),
        91638794 : AssetConfig("AF-BANK-WBTC-STANDARD", 91638794, 6),
        91634691 : AssetConfig("WSOL", 91634691, 6),
        91638864 : AssetConfig("AF-BANK-WSOL-STANDARD", 91638864, 6),
        91639146 : AssetConfig("AF-BANK-ALGO-VAULT", 91639146, 6),
        91634578 : AssetConfig("STBL", 91634578, 6),
        91638952 : AssetConfig("AF-BANK-STBL-STBL", 91638952, 6),
        91634736 : AssetConfig("BANK", 91634736, 6),
        91639074 : AssetConfig("AF-BANK-BANK-STANDARD", 91639074, 6),
    }
}