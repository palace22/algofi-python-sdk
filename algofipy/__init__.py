"""
This module contains all the relevant classes and data for interacting with the Algofi Protocol
"""

# imports
from . import amm
from . import governance
from . import interfaces
from . import lending
from . import staking
from . import algofi_client
from . import algofi_user
from . import asset_amount
from . import asset_config
from . import globals
from . import state_utils
from . import transaction_utils
from . import utils

# metadata
__all__ = [
    "lending",
    "amm",
    "staking",
    "interfaces",
    "governance",
    "algofi_client",
    "algofi_user",
    "asset_amount",
    "asset_config",
    "globals",
    "state_utils",
    "transaction_utils",
    "utils",
]
__version__ = "2.4.2"
__author__ = "Algofi, Inc."
