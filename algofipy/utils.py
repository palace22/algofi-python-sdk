# IMPORTS

# external
from algosdk import account, mnemonic

# FUNCTIONS

def int_to_bytes(num):
    """Int to convert to bytes.

    :param num: int to convert
    :type num: int
    :return: bytes conversion of int
    :rtype: bytes
    """

    return num.to_bytes(8, 'big')

def bytes_to_int(bytes):
    """Bytes to convert to int.

    :param bytes: bytes to convert
    :type bytes: bytes
    :return: int conversion of bytes
    :rtype: int
    """

    return int.from_bytes(bytes, 'big')

def get_new_account():
    """Generate a random Algorand account.

    :return: A newly generated Algorand account (private_key, public_key, passphrase)
    :rtype: (str, str, str)
    """

    key, address = account.generate_account()
    passphrase = mnemonic.from_private_key(key)
    return (key, address, passphrase)

def encode_value(value, type):
    """Encode a value of a given type.

    :param value: value to encode
    :type value: int
    :param type: int or bytes
    :type type: str
    :return: int conversion of bytes
    :rtype: int
    """

    if type == 'int':
        return encode_varint(value)
    raise Exception('Unsupported value type %s!' % type)

def encode_varint(number):
    """Encode an int.

    :param number: number to encode
    :type number: int
    :return: encoded int
    :rtype: bytes
    """

    buf = b''
    while True:
        towrite = number & 0x7f
        number >>= 7
        if number:
            buf += bytes([towrite | 0x80])
        else:
            buf += bytes([towrite])
            break
    return buf