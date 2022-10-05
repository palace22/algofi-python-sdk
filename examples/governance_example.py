import os

from algosdk import mnemonic, account
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import dotenv_values

from algofipy.algofi_client import AlgofiClient
from algofipy.globals import Network
from algofipy.transaction_utils import wait_for_confirmation, get_payment_txn, get_default_params

#my_path = os.path.abspath(os.path.dirname(__file__))
#ENV_PATH = os.path.join(my_path, "../.env")
ENV_PATH = "/home/ubuntu/algofi-python-sdk/examples/.env"

# load user passphrase
env_vars = dotenv_values(ENV_PATH)
key = mnemonic.to_private_key(env_vars['mnemonic'])
sender = account.address_from_private_key(key)

algod = AlgodClient("", "https://node.testnet.algoexplorerapi.io", headers={"User-Agent": "algosdk"})
indexer = IndexerClient("", "https://algoindexer.testnet.algoexplorerapi.io/", headers={'User-Agent': 'algosdk'})
client = AlgofiClient(Network.TESTNET, algod, indexer)

user = client.get_user(sender)

# lock into voting escrow
