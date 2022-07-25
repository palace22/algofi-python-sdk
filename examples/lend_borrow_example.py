import os

from algosdk import mnemonic, account
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import dotenv_values

from algofipy.algofi_client import AlgofiClient
from algofipy.globals import Network
from algofipy.lending.v2.lending_config import MarketType
from algofipy.transaction_utils import wait_for_confirmation

my_path = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(my_path, "../.env")

# load user passphrase
env_vars = dotenv_values(ENV_PATH)
key = mnemonic.to_private_key(env_vars['mnemonic'])
sender = account.address_from_private_key(key)

algod = AlgodClient("", "https://node.algoexplorerapi.io", headers={"User-Agent": "algosdk"})
indexer = IndexerClient("", "https://indexer.algoexplorerapi.io/", headers={'User-Agent': 'algosdk'})
client = AlgofiClient(Network.MAINNET_CLONE2, algod, indexer)

user = client.get_user(sender)
manager = client.lending.manager

algo_market_app_id = 802880734
usdc_market_app_id = 802881530

algo_market = client.lending.markets[algo_market_app_id]
usdc_market = client.lending.markets[usdc_market_app_id]

# ASSET OPT IN
print("opt into assets")
if not user.is_opted_in_to_asset(algo_market.b_asset_id):
    txn = algo_market.get_b_asset_opt_in_txn(user)
    signedTxn = txn.sign(key)
    txid = algod.send_transaction(signedTxn)
    wait_for_confirmation(algod, txid)

if not user.is_opted_in_to_asset(usdc_market.b_asset_id):
    txn = usdc_market.get_b_asset_opt_in_txn(user)
    signedTxn = txn.sign(key)
    txid = algod.send_transaction(signedTxn)
    wait_for_confirmation(algod, txid)

if not user.is_opted_in_to_asset(usdc_market.underlying_asset_id):
    txn = usdc_market.get_underlying_asset_opt_in_txn(user)
    signedTxn = txn.sign(key)
    txid = algod.send_transaction(signedTxn)
    wait_for_confirmation(algod, txid)

print("mint")
# MINT BANK ASSET (NO NEED TO OPT IN)
group = algo_market.get_mint_txns(user.lending, int(1e3))
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# MANAGER OPT IN
print("opt in manager")
if not user.lending.opted_in_to_manager:
    storage_key, storage_address = account.generate_account()
    group = manager.get_opt_in_txns(user.lending, storage_address)
    group.sign_with_private_keys([key, storage_key, key])
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

user.load_state()

# MARKET OPT IN
print("opt in market")
if algo_market_app_id not in user.lending.opted_in_markets:
    group = manager.get_market_opt_in_txns(user.lending, algo_market)
    group.sign_with_private_keys([key])
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

if usdc_market_app_id not in user.lending.opted_in_markets:
    group = manager.get_market_opt_in_txns(user.lending, usdc_market)
    group.sign_with_private_keys([key])
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

user.load_state()

# ADD BANK ASSET COLLATERAL
print("add b asset collateral")
user.load_state()
b_algo_balance = user.balances[algo_market.b_asset_id]
group = algo_market.get_add_b_asset_collateral_txns(user.lending, b_algo_balance)
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# ADD UNDERLYING COLLATERAL
print("add underlying collateral")
group = algo_market.get_add_underlying_collateral_txns(user.lending, int(1e6))
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# BORROW
print("borrow")
group = usdc_market.get_borrow_txns(user.lending,  int(1e3))
group.sign_with_private_keys([key] * group.length())
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# REPAY BORROW
print("repay")
group = algo_market.get_repay_borrow_txns(user.lending, int(1e3+1))
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# REMOVE UNDERLYING COLLATERAL
print("remove underlying collateral")
group = algo_market.get_remove_underlying_collateral_txns(user.lending, int(5e5))
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# REMOVE BANK ASSET COLLATERAL
print("remove b asset collateral")
group = algo_market.get_remove_b_asset_collateral_txns(user.lending, int(5e5))
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# BURN
print("burn")
group = algo_market.get_burn_txns(user.lending, int(1e3))
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

print("claim rewards")
group = algo_market.get_claim_rewards_txns(user.lending,  0)
group.sign_with_private_keys([key] * group.length())
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# OPT OUT
print("opt out markets")
for market in user.lending.opted_in_markets:
    group = manager.get_market_opt_out_txns(user.lending, market)
    group.sign_with_private_keys([key])
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

print("opt out manager")
group = manager.get_manager_opt_out_txns(user.lending, algo_market)
group.sign_with_private_keys([key])
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

