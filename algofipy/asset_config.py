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
    }
}