import os

from algosdk import mnemonic, account
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import dotenv_values

from algofipy.algofi_client import AlgofiClient
from algofipy.globals import Network
from algofipy.amm.v1.amm_config import PoolType, PoolStatus
from algofipy.amm.v1.asset import Asset
from algofipy.transaction_utils import wait_for_confirmation, get_payment_txn, get_default_params
from algofipy.utils import create_asset_transaction

#my_path = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = "/home/ubuntu/algofi-python-sdk/examples/.env"

# load user passphrase
env_vars = dotenv_values(ENV_PATH)
key = mnemonic.to_private_key(env_vars['mnemonic'])
sender = account.address_from_private_key(key)

algod = AlgodClient("", "https://node.algoexplorerapi.io", headers={"User-Agent": "algosdk"})
indexer = IndexerClient("", "https://algoindexer.algoexplorerapi.io/", headers={'User-Agent': 'algosdk'})
client = AlgofiClient(Network.MAINNET, algod, indexer)

user = client.get_user(sender)

lending_pool_app_id = 841198034
lending_pool = client.interfaces.lending_pools[lending_pool_app_id]

# pool
input_asset_id = 31566704
input_asset_amount = 10 
quote = lending_pool.get_pool_quote(input_asset_id, input_asset_amount)
max_slippage = 500000
txn = lending_pool.get_pool_txns(user, quote, max_slippage, False)
txn.sign_with_private_keys([key]*3 + [PERMISSIONLESS_SENDER_LOGIC_SIG]*6, [False]*3+ [True]*6)
txn.submit(client.algod)

# burn
burn_amount = 10
quote = lending_pool.get_burn_quote(burn_amount)
txn = lending_pool.get_burn_txns(user, quote) 
txn.sign_with_private_keys([key]*2 + [PERMISSIONLESS_SENDER_LOGIC_SIG]*3, [False]*2+ [True]*3)
txn.submit(client.algod)

# swap
input_asset_id = 31566704
input_asset_amount = 10 
quote = lending_pool.get_swap_exact_for_quote(input_asset_id, input_asset_amount)
max_slippage = 0.02
txn = lending_pool.get_swap_txns(user, quote, max_slippage)
txn.sign_with_private_keys([key]*2 + [PERMISSIONLESS_SENDER_LOGIC_SIG]*4, [False]*2+ [True]*4)
txn.submit(client.algod)