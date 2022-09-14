import os

from algosdk import mnemonic, account
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import dotenv_values

from algofipy.algofi_client import AlgofiClient
from algofipy.globals import Network
from algofipy.transaction_utils import wait_for_confirmation

#my_path = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = "/home/jaclarke/algofi-python-sdk/examples/.env"

# load user passphrase
env_vars = dotenv_values(ENV_PATH)
key = mnemonic.to_private_key(env_vars['mnemonic'])
sender = account.address_from_private_key(key)

algod = AlgodClient("", "https://node.algoexplorerapi.io", headers={"User-Agent": "algosdk"})
indexer = IndexerClient("", "https://algoindexer.algoexplorerapi.io/", headers={'User-Agent': 'algosdk'})
client = AlgofiClient(Network.MAINNET, algod, indexer)

user = client.get_user(sender)
manager = client.lending.manager

algo_market_app_id = 818179346
usdc_market_app_id = 841145020
stbl2_market_app_id = 841145020

algo_market = client.lending.markets[algo_market_app_id]
usdc_market = client.lending.markets[usdc_market_app_id]
stbl2_market = client.lending.markets[stbl2_market_app_id]

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

if not user.is_opted_in_to_asset(stbl2_market.b_asset_id):
    txn = stbl2_market.get_b_asset_opt_in_txn(user)
    signedTxn = txn.sign(key)
    txid = algod.send_transaction(signedTxn)
    wait_for_confirmation(algod, txid)

if not user.is_opted_in_to_asset(stbl2_market.underlying_asset_id):
    txn = stbl2_market.get_underlying_asset_opt_in_txn(user)
    signedTxn = txn.sign(key)
    txid = algod.send_transaction(signedTxn)
    wait_for_confirmation(algod, txid)

print("mint")
# MINT BANK ASSET (NO NEED TO OPT IN)
group = algo_market.get_mint_txns(user.lending, int(1e3))
group.sign_with_private_key(key)
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
    group.sign_with_private_key(key)
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

if usdc_market_app_id not in user.lending.opted_in_markets:
    group = manager.get_market_opt_in_txns(user.lending, usdc_market)
    group.sign_with_private_key(key)
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

if stbl2_market_app_id not in user.lending.opted_in_markets:
    group = manager.get_market_opt_in_txns(user.lending, stbl2_market)
    group.sign_with_private_key(key)
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

user.load_state()

# ADD BANK ASSET COLLATERAL
print("add b asset collateral")
b_algo_balance = user.balances[algo_market.b_asset_id]
group = algo_market.get_add_b_asset_collateral_txns(user.lending, b_algo_balance)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# ADD UNDERLYING COLLATERAL
print("add underlying collateral")
group = algo_market.get_add_underlying_collateral_txns(user.lending, int(1e6))
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# BORROW
print("borrow")
group = stbl2_market.get_borrow_txns(user.lending,  int(1e3))
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# REPAY BORROW
print("repay")
# ADD A USDC BUFFER TO YOUR WALLET
group = stbl2_market.get_repay_borrow_txns(user.lending, int(1e2))
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# REMOVE UNDERLYING COLLATERAL
print("remove underlying collateral")
group = algo_market.get_remove_underlying_collateral_txns(user.lending, int(1e2))
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# REMOVE BANK ASSET COLLATERAL
print("remove b asset collateral")
user.load_state()
b_asset_amount = user.lending.user_market_states[algo_market_app_id].b_asset_collateral
group = algo_market.get_remove_b_asset_collateral_txns(user.lending, b_asset_amount)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# BURN
print("burn")
group = algo_market.get_burn_txns(user.lending, int(1e3))
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

print("claim rewards")
group = algo_market.get_claim_rewards_txns(user.lending,  0)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# CLOSE OUT
print("close out markets")
group = manager.get_market_close_out_txns(user.lending, algo_market)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

user.load_state()

group = manager.get_market_close_out_txns(user.lending, stbl2_market)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

user.load_state()

group = manager.get_market_close_out_txns(user.lending, usdc_market)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

user.load_state()

print("close out manager")
group = manager.get_close_out_txns(user.lending)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)