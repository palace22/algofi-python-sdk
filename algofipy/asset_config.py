# IMPORTS

# global
from algofipy.globals import Network

# INTERFACE


class AssetConfig:
    def __init__(self, name, asset_id, decimals):
        """Asset config storing asset information for a given asset id

        :param name: underlying amount of asset
        :type name: int
        :param asset_id: asset id
        :type asset_id: int
        :param decimals: number of decimals in the asset
        :type decimals: int
        """

        self.name = name
        self.asset_id = asset_id
        self.decimals = decimals


ASSET_CONFIGS = {
    Network.MAINNET: {
        1: AssetConfig("ALGO", 1, 6),
        818179690: AssetConfig("AF-BANK-ALGO-STANDARD", 818179690, 6),
        31566704: AssetConfig("USDC", 31566704, 6),
        818182311: AssetConfig("AF-BANK-USDC-STANDARD", 818182311, 6),
        386192725: AssetConfig("GOBTC", 386192725, 8),
        818184214: AssetConfig("AF-BANK-GOBTC-STANDARD", 818184214, 6),
        386195940: AssetConfig("GOETH", 386195940, 8),
        818188553: AssetConfig("AF-BANK-GOETH-STANDARD", 818188553, 6),
        312769: AssetConfig("USDT", 312769, 6),
        818190568: AssetConfig("AF-BANK-USDT-STANDARD", 818190568, 6),
        841126810: AssetConfig("STBL2", 841126810, 6),
        841157954: AssetConfig("AF-BANK-STBL2-STABLE", 841157954, 6),
        879951266: AssetConfig("AF-BANK-ALGO-VAULT", 879951266, 6),
        841171328: AssetConfig("AF-NANO-POOL-AF-BANK-AF-BANK", 841171328, 6),
        841462373: AssetConfig("AF-BANK-AF-POOL-LP", 841462373, 6),
        855717054: AssetConfig("AF-NANO-POOL-AF-BANK-AF-BANK", 855717054, 6),
        856217307: AssetConfig("AF-BANK-AF-POOL-LP", 856217307, 6),
        870151164: AssetConfig("AF-NANO-POOL-AF-BANK-AF-BANK", 870151164, 6),
        870380101: AssetConfig("AF-BANK-AF-POOL-LP", 870380101, 6),
        870150187: AssetConfig("AF-NANO-POOL-AF-BANK-AF-BANK", 870150187, 6),
        870391958: AssetConfig("AF-BANK-AF-POOL-LP", 870391958, 6),
        900652777: AssetConfig("BANK", 900652777, 6),
    },
    Network.TESTNET: {
        1: AssetConfig("ALGO", 1, 6),
        107212062: AssetConfig("BANK", 107212062, 6),
        104193939: AssetConfig("AF-BANK-ALGO-STANDARD", 104193939, 6),
        104194013: AssetConfig("USDC", 104194013, 6),
        104207173: AssetConfig("AF-BANK-USDC-STANDARD", 104207173, 6),
        104207287: AssetConfig("goBTC", 104207287, 8),
        104207503: AssetConfig("AF-BANK-GOBTC-STANDARD", 104207503, 6),
        104207533: AssetConfig("goETH", 104207533, 8),
        104207983: AssetConfig("AF-BANK-GOETH-STANDARD", 104207983, 6),
        104208050: AssetConfig("USDT", 104208050, 6),
        104222974: AssetConfig("AF-BANK-USDT-STANDARD", 104222974, 6),
        104210500: AssetConfig("STBL2", 104210500, 6),
        104217422: AssetConfig("AF-BANK-STBL2-STABLE", 104217422, 6),
        104228491: AssetConfig("AF-bUSDC-bSTBL2-NANO-LP", 104228491, 6),
        104238470: AssetConfig("AF-BANK-AF-bUSDC-bSTBL2-NANO-LP-LP", 104238470, 6),
    },
}
