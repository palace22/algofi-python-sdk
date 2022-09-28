
# IMPORTS

# external
from enum import Enum
from base64 import b64encode

# local
from .approval_programs import MAINNET_APPROVAL_PROGRAM_25BP_CONSTANT_PRODUCT, MAINNET_APPROVAL_PROGRAM_75BP_CONSTANT_PRODUCT, \
    TESTNET_APPROVAL_PROGRAM_30BP_CONSTANT_PRODUCT, TESTNET_APPROVAL_PROGRAM_100BP_CONSTANT_PRODUCT, CLEAR_STATE_PROGRAM

# INTERFACE

# constants
ALGO_ASSET_ID = 1
PARAMETER_SCALE_FACTOR = 1000000

# nanoswap pools
TESTNET_NANOSWAP_POOLS = {
    (77279127, 77279142): 77282939
}  # (asset1_id, asset2_id) -> app_id
MAINNET_NANOSWAP_POOLS = {
    (31566704, 465865291): 658337046,
    (312769, 465865291): 659677335,
    (312769, 31566704): 659678644,
    (818182311, 841157954): 841170409,
}
NANOSWAP_MANAGER = {
    (31566704, 465865291): 658336870,
    (312769, 465865291): 658336870,
    (312769, 31566704): 658336870,
    (818182311, 841157954): 841165954,
}
LENDING_POOLS = {
    (818179690, 841157954): 855716333,
    (818184214, 841157954): 870150391,
    (818188553, 841157954): 870143131
}
LENDING_POOLS_MANAGER = {
    (818179690, 841157954): 841165954,
    (818184214, 841157954): 841165954,
    (818188553, 841157954): 841165954
}

# enums
class Network(Enum):
    """Network enum
    """
    MAINNET = 0
    TESTNET = 1


class PoolType(Enum):
    """Pool type enum
    """
    CONSTANT_PRODUCT_25BP_FEE = 1
    CONSTANT_PRODUCT_30BP_FEE = 2
    CONSTANT_PRODUCT_75BP_FEE = 3
    CONSTANT_PRODUCT_100BP_FEE = 4
    NANOSWAP = 5


class PoolStatus(Enum):
    """Pool status enum
    """
    UNINITIALIZED = 0
    ACTIVE = 1


# lookup functions
def get_validator_index(network, pool_type):
    """Gets the validator index for a given pool type and network

    :param network: network :class:`Network` ("testnet" or "mainnet")
    :type network: str
    :param pool_type: a :class:`PoolType` object for the type of pool (e.g. 30bp, 100bp fee)
    :type pool_type: :class:`PoolType`
    :return: validator index for given type of pool
    :rtype: int
    """

    if network == Network.MAINNET:
        if (pool_type == PoolType.CONSTANT_PRODUCT_25BP_FEE):
            return 0
        elif (pool_type == PoolType.CONSTANT_PRODUCT_75BP_FEE):
            return 1
    elif network == Network.TESTNET:
        if (pool_type == PoolType.CONSTANT_PRODUCT_30BP_FEE):
            return 0
        elif (pool_type == PoolType.CONSTANT_PRODUCT_100BP_FEE):
            return 1
        elif (pool_type == PoolType.NANOSWAP):
            return -1


def get_approval_program_by_pool_type(pool_type, network):
    """Gets the approval program for a given pool type

    :param pool_type: a :class:`PoolType` object for the type of pool (e.g. 30bp, 100bp fee)
    :type pool_type: :class:`PoolType`
    :param pool_type: a :class:`PoolType` object for the type of pool (e.g. 30bp, 100bp fee)
    :type pool_type: :class:`PoolType`
    :return: approval program bytecode for given pool type as list of ints
    :rtype: list
    """

    if network == Network.MAINNET:
        if (pool_type == PoolType.CONSTANT_PRODUCT_25BP_FEE):
            return bytes(MAINNET_APPROVAL_PROGRAM_25BP_CONSTANT_PRODUCT)
        elif (pool_type == PoolType.CONSTANT_PRODUCT_75BP_FEE):
            return bytes(MAINNET_APPROVAL_PROGRAM_75BP_CONSTANT_PRODUCT)
    elif network == Network.TESTNET:
        if (pool_type == PoolType.CONSTANT_PRODUCT_30BP_FEE):
            return bytes(TESTNET_APPROVAL_PROGRAM_30BP_CONSTANT_PRODUCT)
        elif (pool_type == PoolType.CONSTANT_PRODUCT_100BP_FEE):
            return bytes(TESTNET_APPROVAL_PROGRAM_100BP_CONSTANT_PRODUCT)


def get_clear_state_program():
    """Gets the clear state program

    :return: clear state program bytecode as list of ints
    :rtype: list
    """

    return bytes(CLEAR_STATE_PROGRAM)


def get_manager_application_id(network, pool_key=None):
    """Gets the manager application id for the given network

    :param network: network :class:`Network` ("testnet" or "mainnet")
    :type network: str
    :param pool_key: tuple of (asset1_id, asset2_id)
    :type pool_key: tuple (int, int)
    :return: manager application id for the given network
    :rtype: int
    """

    if (network == Network.MAINNET):
        if pool_key in NANOSWAP_MANAGER:
            return NANOSWAP_MANAGER[pool_key]
        elif pool_key in LENDING_POOLS_MANAGER:
            return LENDING_POOLS_MANAGER[pool_key]
        return 605753404
    elif (network == Network.TESTNET):
        if pool_key:
            return NANOSWAP_MANAGER[pool_key]
        elif pool_key in LENDING_POOLS_MANAGER:
            return LENDING_POOLS_MANAGER[pool_key]
        return 66008735


def get_swap_fee(pool_type):
    """Gets the swap fee for a given pool type

    :param pool_type: a :class:`PoolType` object for the type of pool (e.g. 30bp, 100bp fee)
    :type pool_type: :class:`PoolType`
    :return: swap fee for a given pool type
    :rtype: float
    """

    if (pool_type == PoolType.CONSTANT_PRODUCT_25BP_FEE):
        return 0.0025
    elif (pool_type == PoolType.CONSTANT_PRODUCT_30BP_FEE):
        return 0.003
    elif (pool_type == PoolType.CONSTANT_PRODUCT_75BP_FEE):
        return 0.0075
    elif (pool_type == PoolType.CONSTANT_PRODUCT_100BP_FEE):
        return 0.01
    elif (pool_type == PoolType.NANOSWAP):
        return 0.001


def get_usdc_asset_id(network):
    """Gets asset id of USDC for a given network

    :param network: network :class:`Network` ("testnet" or "mainnet")
    :type network: str
    :return: asset id of USDC for a given network
    :rtype: int
    """

    if (network == Network.MAINNET):
        return 31566704
    elif (network == Network.TESTNET):
        return 51435943


def get_stbl_asset_id(network):
    """Gets asset id of STBL for a given network

    :param network: network :class:`Network` ("testnet" or "mainnet")
    :type network: str
    :return: asset id of STBL for a given network
    :rtype: int
    """

    if (network == Network.MAINNET):
        return 465865291
    elif (network == Network.TESTNET):
        return 51437163

class POOL_STRINGS:
    # user variables
    admin = "a"
    asset1_id = "a1"
    asset_1_to_asset_2_exchange = "e"
    asset2_id = "a2"
    asset1_reserve = "a1r"
    asset2_reserve = "a2r"
    balance_1 = "b1"
    balance_2 = "b2"
    burn_asset1_out = "ba1o"
    burn_asset2_out = "ba2o"
    contract_update_delay = "cud"
    contract_update_time = "cut"
    cumsum_fees_asset1 = "cf1"
    cumsum_fees_asset2 = "cf2"
    cumsum_time_weighted_asset1_to_asset2_price = "ct12"
    cumsum_time_weighted_asset2_to_asset1_price = "ct21"
    cumsum_volume_asset1 = "cv1"
    cumsum_volume_asset2 = "cv2"
    cumsum_volume_weighted_asset1_to_asset2_price = "cv12"
    cumsum_volume_weighted_asset2_to_asset1_price = "cv21"
    flash_loan = "fl"
    flash_loan_fee = "flf"
    increase_contract_update_delay = "icud"
    latest_time = "lt"
    lp_circulation = "lc"
    lp_id = "l"
    manager = "m"
    max_flash_loan_ratio = "mflr"
    opt_into_assets = "o"
    pool = "p"
    redeem_pool_asset1_residual = "rpa1r"
    redeem_pool_asset2_residual = "rpa2r"
    redeem_swap_residual = "rsr"
    remove_reserves = "rr"
    reserve_factor = "rf"
    schedule_contract_update = "scu"
    swap_exact_for = "sef"
    swap_for_exact = "sfe"
    initialized = "i"
    initialize_pool = "ip"
    initial_amplification_factor = "iaf"
    future_amplification_factor = "faf"
    initial_amplification_factor_time = "iat"
    future_amplification_factor_time = "fat"


class MANAGER_STRINGS:
    admin = "a"
    contract_update_delay = "cud"
    contract_update_time = "cut"
    flash_loan_fee = "flf"
    increase_contract_update_delay = "icud"
    initialize_pool = "ip"
    max_flash_loan_ratio = "mflr"
    pool_hash_prefix = "ph_"
    registered_asset_1_id = "a1"
    registered_asset_2_id = "a2"
    registered_pool_id = "p"
    reserve_factor = "rf"
    schedule_contract_update = "scu"
    set_flash_loan_fee = "sflf"
    set_reserve_factor = "srf"
    set_max_flash_loan_ratio = "smflr"
    set_validator = "sv"
    validator_index="vi"

# valid pool app ids
b64_to_utf_keys = {
    b64encode(bytes(POOL_STRINGS.asset1_id, "utf-8")).decode("utf-8"): POOL_STRINGS.asset1_id,
    b64encode(bytes(POOL_STRINGS.asset2_id, "utf-8")).decode("utf-8"): POOL_STRINGS.asset2_id,
    b64encode(bytes(POOL_STRINGS.pool, "utf-8")).decode("utf-8"): POOL_STRINGS.pool,
    b64encode(bytes(MANAGER_STRINGS.validator_index, "utf-8")).decode("utf-8"): MANAGER_STRINGS.validator_index,
    b64encode(bytes(POOL_STRINGS.balance_1, "utf-8")).decode("utf-8"): POOL_STRINGS.balance_1,
    b64encode(bytes(POOL_STRINGS.balance_2, "utf-8")).decode("utf-8"): POOL_STRINGS.balance_2,
    b64encode(bytes(POOL_STRINGS.cumsum_volume_asset1, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_volume_asset1,
    b64encode(bytes(POOL_STRINGS.cumsum_volume_asset2, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_volume_asset2,
    b64encode(bytes(POOL_STRINGS.cumsum_volume_weighted_asset1_to_asset2_price, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_volume_weighted_asset1_to_asset2_price,
    b64encode(bytes(POOL_STRINGS.cumsum_volume_weighted_asset2_to_asset1_price, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_volume_weighted_asset2_to_asset1_price,
    b64encode(bytes(POOL_STRINGS.cumsum_time_weighted_asset2_to_asset1_price, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_time_weighted_asset2_to_asset1_price,
    b64encode(bytes(POOL_STRINGS.cumsum_time_weighted_asset1_to_asset2_price, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_time_weighted_asset1_to_asset2_price,
    b64encode(bytes(POOL_STRINGS.cumsum_fees_asset1, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_fees_asset1,
    b64encode(bytes(POOL_STRINGS.cumsum_fees_asset2, "utf-8")).decode("utf-8"): POOL_STRINGS.cumsum_fees_asset2
}

utf_to_b64_keys = {v: k for k, v in b64_to_utf_keys.items()}
