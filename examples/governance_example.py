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

## Voting Escrow
voting_escrow = client.governance.voting_escrow

# opt into voting escrow
if not user.governance.opted_into_governance:
    (storage_private_key, storage_address) = account.generate_account()
    txn = client.governance.get_opt_in_txns(user, storage_address)
    txn.sign_with_private_keys([key, storage_private_key, key, key, key])
    txn.submit(algod, wait=True)

# lock into voting escrow
txn = voting_escrow.get_lock_txns(user, amount=100_000_000, duration_seconds=int(60*2))
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# extend lock
txn = voting_escrow.get_extend_lock_txns(user, duration_seconds=int(60*2))
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

# set open to delegation
txn = admin.get_set_open_to_delegation_txns(user)
txn.sign_with_private_key(key)
txn.submit(algod, wait=True)

# set not open to delegation
txn = admin.get_set_not_open_to_delegation_txns(user)
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
proposal = client.governance.admin.proposals[113295284]
txn = admin.get_vote_txns(user, proposal, 1)