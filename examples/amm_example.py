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

my_path = os.path.abspath(os.path.dirname(__file__))
ENV_PATH = os.path.join(my_path, "../.env")

# load user passphrase
env_vars = dotenv_values(ENV_PATH)
key = mnemonic.to_private_key(env_vars['mnemonic'])
sender = account.address_from_private_key(key)

algod = AlgodClient("", "https://node.algoexplorerapi.io", headers={"User-Agent": "algosdk"})
indexer = IndexerClient("", "https://algoindexer.algoexplorerapi.io/", headers={'User-Agent': 'algosdk'})
client = AlgofiClient(Network.MAINNET, algod, indexer)

user = client.get_user(sender)

# create a pool
# first create two test assets or fill in asset1 and asset2
asset1_id = 843595609
asset2_id = 843595712
asset1 = Asset(client.amm, asset1_id)
asset2 = Asset(client.amm, asset2_id)

if not asset1_id:
    create_test_asset1_txn = create_asset_transaction(
        algod,
        user.address, 
        total=int(1e19),
        decimals=6,
        default_frozen=False,
        manager=user.address,
        reserve=user.address,
        freeze=user.address,
        clawback=user.address,
        unit_name="TEST1",
        asset_name="TEST1",
        url="https://test.com"
    )
    txid = algod.send_transaction(create_test_asset1_txn.sign(key))
    wait_for_confirmation(algod, txid)
    asset1_id = algod.pending_transaction_info(txid)["asset-index"]

if not asset2_id:
    create_test_asset2_txn = create_asset_transaction(
        algod,
        user.address, 
        total=int(1e19),
        decimals=6,
        default_frozen=False,
        manager=user.address,
        reserve=user.address,
        freeze=user.address,
        clawback=user.address,
        unit_name="TEST2",
        asset_name="TEST2",
        url="https://test.com"
    )
    txid = algod.send_transaction(create_test_asset2_txn.sign(key))
    wait_for_confirmation(algod, txid)
    asset2_id = algod.pending_transaction_info(txid)["asset-index"]

# get pool data
pool_type = PoolType.CONSTANT_PRODUCT_25BP_FEE
pool = client.amm.get_pool(pool_type, asset1_id, asset2_id)

# create + initialize pool if it is not created yet
if pool.pool_status == PoolStatus.UNINITIALIZED:
    group = pool.get_create_pool_txn(user.address)
    group.sign_with_private_key(key)
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)

    pool_app_id = algod.pending_transaction_info(txid)["application-index"]

    group = pool.get_initialize_pool_txns(user.address, pool_app_id)
    group.sign_with_private_keys([key, key]+[pool.logic_sig, key], [False, False, True, False])
    txid = algod.send_transactions(group.signed_transactions)
    wait_for_confirmation(algod, txid)
    pool.refresh_metadata()
    pool.refresh_state()

# opt into lp token if you're not opted in yet
if not user.is_opted_in_to_asset(pool.lp_asset_id):
    stxn = pool.get_lp_token_opt_in_txn(user.address).sign(key)
    txid = algod.send_transaction(stxn)
    wait_for_confirmation(algod, txid)

# pool assets with the ratio of assets you specify
asset1_amount = int(10e6)
asset2_amount = int(20e6)
group = pool.get_pool_txns(
    user.address,
    asset1_amount,
    asset2_amount,
    maximum_slippage=int(1000)
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# burn lp tokens in the amount you specify
burn_amount = int(0.5e6)
group = pool.get_burn_txns(
    user.address,
    burn_amount
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# swap exact for in the amount of swap asset you specify
swap_in_asset = asset1
swap_in_amount = int(0.5e6)
group = pool.get_swap_exact_for_txns(
    user.address,
    swap_in_asset,
    swap_in_amount,
    min_amount_to_receive=0
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# swap for exact in the amount of the exact asset you specify
swap_in_asset = asset1
swap_in_amount = int(0.5e6)
amount_to_receive = int(0.2e6)
group = pool.get_swap_for_exact_txns(
    user.address,
    swap_in_asset,
    swap_in_amount,
    amount_to_receive
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# execute a flash loan
swap_in_asset = asset1
swap_in_amount = int(0.1e6)
group = pool.get_swap_exact_for_txns(
    user.address,
    swap_in_asset,
    swap_in_amount,
    min_amount_to_receive=0
)
group = pool.get_flash_loan_txns(
    user.address,
    swap_in_asset,
    swap_in_amount,
    group_transaction=group
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# -----------------------------------------------------------
# nanoswap operations for specified assets
asset1_id = 818182311
asset2_id = 841157954
asset1 = Asset(client.amm, asset1_id)
asset2 = Asset(client.amm, asset2_id)

pool_type = PoolType.NANOSWAP
pool = client.amm.get_pool(pool_type, asset1_id, asset2_id)

# opt into underlying assets if required
if not user.is_opted_in_to_asset(asset1_id):
    stxn = get_payment_txn(
        user.address,
        get_default_params(algod),
        user.address,
        int(0),
        asset_id=asset1_id
    ).sign(key)
    txid = algod.send_transaction(stxn)
    wait_for_confirmation(algod, txid)

if not user.is_opted_in_to_asset(asset2_id):
    stxn = get_payment_txn(
        user.address,
        get_default_params(algod),
        user.address,
        int(0),
        asset_id=asset2_id
    ).sign(key)
    txid = algod.send_transaction(stxn)
    wait_for_confirmation(algod, txid)

# opt into lp token if you're not opted in yet
if not user.is_opted_in_to_asset(pool.lp_asset_id):
    stxn = pool.get_lp_token_opt_in_txn(user.address).sign(key)
    txid = algod.send_transaction(stxn)
    wait_for_confirmation(algod, txid)

# pool assets to nanoswap pool
asset1_amount = int(0.1e6)
asset2_amount = int(0.1e6)
group = pool.get_pool_txns(
    user.address,
    asset1_amount,
    asset2_amount,
    maximum_slippage=int(100000)
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# burn lp tokens in the amount you specify
burn_amount = int(0.1e6)
group = pool.get_burn_txns(
    user.address,
    burn_amount
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# swap exact for in the amount of swap asset you specify
swap_in_asset = asset2
swap_in_amount = int(10)
group = pool.get_swap_exact_for_txns(
    user.address,
    swap_in_asset,
    swap_in_amount,
    min_amount_to_receive=0,
    fee=5000
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)

# swap for exact in the amount of the exact asset you specify
swap_in_asset = asset1
swap_in_amount = int(100)
amount_to_receive = int(10)
group = pool.get_swap_for_exact_txns(
    user.address,
    swap_in_asset,
    swap_in_amount,
    amount_to_receive,
    fee=5000
)
group.sign_with_private_key(key)
txid = algod.send_transactions(group.signed_transactions)
wait_for_confirmation(algod, txid)