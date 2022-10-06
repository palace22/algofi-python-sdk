import os
import time

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

algod = AlgodClient("", "https://node.testnet.algoexplorerapi.io", headers={"User-Agent": "algosdk"})
indexer = IndexerClient("", "https://algoindexer.testnet.algoexplorerapi.io/", headers={'User-Agent': 'algosdk'})
client = AlgofiClient(Network.TESTNET, algod, indexer)

# load user passphrase
env_vars = dotenv_values(ENV_PATH)
MNEMONICS=["user1", "user2", "user3", "user4"]
user_keys = {}
for user_key in MNEMONICS:
    key = mnemonic.to_private_key(env_vars[user_key])
    sender = account.address_from_private_key(key)
    user = client.get_user(sender)
    user_keys[user_key] = {"key": key, "sender": sender, "user": user}

## Voting Escrow
voting_escrow = client.governance.voting_escrow

# opt into voting escrow
for user_key in user_keys:
    key, user = user_keys[user_key]["key"], user_keys[user_key]["user"]
    if not user.governance.opted_into_governance:
        (storage_private_key, storage_address) = account.generate_account()
        txn = client.governance.get_opt_in_txns(user, storage_address)
        txn.sign_with_private_keys([key, storage_private_key, key, key, key])
        txn.submit(algod, wait=True)

key, user = user_keys["user1"]["key"], user_keys["user1"]["user"]

# lock into voting escrow
txn = voting_escrow.get_lock_txns(user, amount=100_000_000, duration_seconds=int(60*5))
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# extend lock
txn = voting_escrow.get_extend_lock_txns(user, duration_seconds=int(60*4))
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# increase lock amount
txn = voting_escrow.get_increase_lock_amount_txns(user, amount=1_000_000)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# update a user's vebank
txn = voting_escrow.get_update_vebank_data_txns(user, user)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# claim voting escrow assets
txn = voting_escrow.get_claim_txns(user)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

## Admin
admin = client.governance.admin

# set not open to delegation
txn = admin.get_set_not_open_to_delegation_txns(user)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# set open to delegation
txn = admin.get_set_open_to_delegation_txns(user)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# delegate
user2 = user_keys["user2"]["user"]
txn = admin.get_delegate_txns(user=user, delegatee=user2)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# undelegate
txn = admin.get_undelegate_txns(user)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

print("Number of proposals ", len(client.governance.admin.proposals))
# create a proposal
txn = admin.get_create_proposal_txns(user, title="test123", link="testlink")
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)
client.governance.admin.load_state()
print("Number of proposals ", len(client.governance.admin.proposals))

# vote on proposal
PROPOSAL_APP_ID = max(list(client.governance.admin.proposals.keys())) 
proposal = client.governance.admin.proposals[PROPOSAL_APP_ID]
txn = admin.get_vote_txns(user, proposal, 1)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# claim && lock vebank & undelegate & set not open to delegation & delegate to a user
for i in range(2, 5):
    user_key = "user"+str(i)
    user_, key_ = user_keys[user_key]["user"], user_keys[user_key]["key"]
    # update user
    user_.load_state()
    # claim
    lock_end_time = user_.governance.user_voting_escrow_state.lock_start_time + user_.governance.user_voting_escrow_state.lock_duration
    vebank = user_.governance.user_voting_escrow_state.amount_vebank
    if lock_end_time != 0 and int(time.time()) > lock_end_time and vebank > 0:
        txn = voting_escrow.get_claim_txns(user_)
        txn.sign_with_private_key(key_)
        txn.submit(algod, wait=True)
        # lock vebank
        txn = voting_escrow.get_lock_txns(user_, amount=100_000_000, duration_seconds=int(60*5))
        txn.sign_with_private_key(key_)
        txn.submit(algod, wait=False)
    else:
        delta = (lock_end_time - int(time.time())) - 5 * 60 - 10
        if delta > 0:
            txn = voting_escrow.get_extend_lock_txns(user_, duration_seconds=int(delta))
            txn.sign_with_private_key(key_)
            txn.submit(algod, wait=True)
    # undelegate
    if user_.governance.user_admin_state.delegating_to:
        txn = admin.get_undelegate_txns(user_)
        txn.sign_with_private_key(key_)
        txn.submit(algod, wait=False)
    # set not open to delegation
    txn = admin.get_set_not_open_to_delegation_txns(user_)
    txn.sign_with_private_key(key_)
    txn.submit(algod, wait=True)
    # delegate
    txn = admin.get_delegate_txns(user=user_, delegatee=user)
    txn.sign_with_private_key(key_)
    txn.submit(algod, wait=False)

# delegate voted
for i in range(2, 5):
    user_key = "user"+str(i)
    user_, key_ = user_keys[user_key]["user"], user_keys[user_key]["key"]
    txn = admin.get_delegated_vote_txns(calling_user=user, voting_user=user_, proposal=proposal)
    txn.sign_with_private_key(key)
    txn.submit(algod, wait=True)

# update user ve bank
txn = admin.get_update_user_vebank_txns(user, user)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)