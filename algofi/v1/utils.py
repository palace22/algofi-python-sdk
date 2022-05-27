# IMPORTS

# external
from algosdk import account, mnemonic

# FUNCTIONS

def int_to_bytes(num):
    return num.to_bytes(8, 'big')

def get_new_account():
    key, address = account.generate_account()
    passphrase = mnemonic.from_private_key(key)
    return (key, address, passphrase)

def encode_value(value, type):
    if type == 'int':
        return encode_varint(value)
    raise Exception('Unsupported value type %s!' % type)

def encode_varint(number):
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