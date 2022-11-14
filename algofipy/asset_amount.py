# IMPORTS

# INTERFACE


class AssetAmount:
    def __init__(self, underlying, usd):
        """A client for the algofi protocol

        :param underlying: underlying amount of asset
        :type underlying: int
        :param usd: usd amount of asset
        :type usd: int
        """

        self.underlying = underlying
        self.usd = usd
