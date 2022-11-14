# IMPORTS

# external
from functools import reduce

# local

# INTERFACE

# pool factory logic sig template and indexes
POOL_FACTORY_LOGIC_SIG_TEMPLATE_1 = [5, 32, 3]
POOL_FACTORY_LOGIC_SIG_TEMPLATE_2 = [
    1,
    34,
    35,
    12,
    68,
    49,
    16,
    129,
    6,
    18,
    68,
    49,
    25,
    36,
    18,
    68,
    49,
    24,
    129,
]
POOL_FACTORY_LOGIC_SIG_TEMPLATE_3 = [
    18,
    68,
    54,
    26,
    0,
    23,
    34,
    18,
    68,
    54,
    26,
    1,
    23,
    35,
    18,
    68,
    54,
    26,
    2,
    23,
    129,
]
POOL_FACTORY_LOGIC_SIG_TEMPLATE_4 = [18, 68, 49, 32, 50, 3, 18, 68, 36, 67]


def encode_varint(integer):
    """Returns bytecode representation of a TEAL Int from an integer

    :param integer: integer to encode
    :type integer: int
    :return: list of ints representing bytecode representation of TEAL Int
    :rtype: list
    """
    buf = b""
    while True:
        towrite = integer & 0x7F
        integer >>= 7
        if integer:
            buf += bytes([towrite | 0x80])
        else:
            buf += bytes([towrite])
            break
    return buf


def generate_logic_sig(asset1_id, asset2_id, manager_app_id, validator_index):
    """Returns a boolean if the user address is opted into an application with id app_id

    :param asset1_id: asset id of first asset in pool
    :type asset1_id: int
    :param asset1_id: asset id of second asset in pool
    :type asset1_id: int
    :param manager_app_id: application id of manager
    :type manager_app_id: int
    :param validator_index: validator index for type of pool
    :type validator_index: int
    :return: list of ints representing bytecode representation of logic sig
    :rtype: list
    """

    concat_array = [
        POOL_FACTORY_LOGIC_SIG_TEMPLATE_1,
        list(encode_varint(asset1_id)),
        list(encode_varint(asset2_id)),
        POOL_FACTORY_LOGIC_SIG_TEMPLATE_2,
        list(encode_varint(manager_app_id)),
        POOL_FACTORY_LOGIC_SIG_TEMPLATE_3,
        list(encode_varint(validator_index)),
        POOL_FACTORY_LOGIC_SIG_TEMPLATE_4,
    ]
    logic_sig_list_of_ints = list(reduce(lambda x, y: x + y, concat_array))
    logic_sig_bytes = bytes(logic_sig_list_of_ints)

    return logic_sig_bytes
