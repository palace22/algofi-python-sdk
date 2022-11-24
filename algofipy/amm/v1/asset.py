# IMPORTS

# external
import pprint
import requests as re

# local
from .amm_config import (
    PoolType,
    PoolStatus,
    Network,
    get_usdc_asset_id,
    get_stbl_asset_id,
    ALGO_ASSET_ID,
    AMMEndpoints,
)

# INTERFACE

# asset decimals
ALGO_DECIMALS = 6
USDC_DECIMALS = 6
STBL_DECIMALS = 6


class Asset:
    def __init__(self, amm_client, asset_id):
        """Constructor method for :class:`Asset`
        :param amm_client: a :class:`AlgofiAMMClient` for interacting with the AMM
        :type amm_client: :class:`AlgofiAMMClient`
        :param asset_id: asset id
        :type asset_id: int
        """

        self.asset_id = asset_id
        self.amm_client = amm_client

        if asset_id == 1:
            self.creator = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
            self.decimals = ALGO_DECIMALS
            self.default_frozen = False
            self.freeze = None
            self.manager = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
            self.name = "Algorand"
            self.reserve = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"
            self.total = 10000000000
            self.unit_name = "ALGO"
            self.url = "https://www.algorand.com/"
        else:
            asset_info = amm_client.indexer.asset_info(asset_id)
            self.creator = asset_info["asset"]["params"]["creator"]
            self.decimals = asset_info["asset"]["params"]["decimals"]
            self.default_frozen = asset_info["asset"]["params"].get(
                "default-frozen", False
            )
            self.freeze = asset_info["asset"]["params"].get("freeze", None)
            self.manager = asset_info["asset"]["params"].get("manager", None)
            self.name = asset_info["asset"]["params"].get("name", None)
            self.reserve = asset_info["asset"]["params"].get("reserve", None)
            self.total = asset_info["asset"]["params"].get("total", None)
            self.unit_name = asset_info["asset"]["params"].get("unit-name", None)
            self.url = asset_info["asset"]["params"].get("url", None)

    def __str__(self):
        """Returns a pretty string representation of the :class:`Asset` object
        :return: string representation of asset
        :rtype: str
        """
        return pprint.pformat(
            {
                "asset_id": self.asset_id,
                "creator": self.creator,
                "decimals": self.decimals,
                "default_frozen": self.default_frozen,
                "freeze": self.freeze,
                "manager": self.manager,
                "name": self.name,
                "reserve": self.reserve,
                "total": self.total,
                "unit_name": self.unit_name,
                "url": self.url,
            }
        )

    def get_scaled_amount(self, amount):
        """Returns an integer representation of asset amount scaled by asset's decimals
        :param amount: amount of asset
        :type amount: float
        :return: int amount of asset scaled by decimals
        :rtype: int
        """

        return int(amount * 10**self.decimals)

    def get_decimal_amount(self, amount):
        """Returns a decimal representation of the input amount
        :param amount: amount of asset in base units
        :type amount: int
        :return: float decimal amount of asset
        :rtype: float
        """

        return amount / 10**self.decimals

    def refresh_price(self):
        """Refreshes the dollar price of the asset"""

        try:
            prices = dict(
                [
                    (x["asset_id"], x["price"])
                    for x in (
                        re.get(AMMEndpoints.ASSETS).json()
                        + re.get(AMMEndpoints.AMM_LP_TOKENS).json()
                    )
                ]
            )
            self.price = prices[self.asset_id]
        except:
            raise Exception(
                "Failed to query price from endpoints "
                + AMMEndpoints.ASSETS
                + " and "
                + AMMEndpoints.AMM_LP_TOKENS
            )

    def to_usd(self, amount):
        """Returns a dollar amount of asset given an amount in base units
        :param amount: amount of asset
        :type amount: float
        :return: decimal dollar amount of asset
        :rtype: float
        """

        self.refresh_price()
        return self.get_decimal_amount(amount) * self.price
