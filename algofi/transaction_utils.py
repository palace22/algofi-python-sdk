# IMPORTS

# external
from algosdk.error import AlgodHTTPError

# local
from algosdk.future.transaction import assign_group_id, PaymentTxn, AssetTransferTxn, LogicSig, LogicSigTransaction

from .globals import ALGO_ASSET_ID

# FUNCTIONS

def get_default_params(algod):
    params = algod.suggested_params()
    params.flat_fee = True
    params.fee = 1000
    return params

def get_payment_txn(sender, params, receiver, amount, asset_id):
    if asset_id == ALGO_ASSET_ID:
        txn = PaymentTxn(sender=sender, sp=params, receiver=receiver, amt=amount)
    else:
        txn = AssetTransferTxn(sender=sender, sp=params, receiver=receiver, amt=amount, index=asset_id)
    return txn

def wait_for_confirmation(algod, txid):
    last_round = algod.status().get('last-round')
    txinfo = algod.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        algod.status_after_block(last_round)
        txinfo = algod.pending_transaction_info(txid)
    txinfo['txid'] = txid
    return txinfo

class TransactionGroup:
    def __init__(self, transactions):
        for t in transactions:
            t.group = None
        transactions = assign_group_id(transactions)
        self.transactions = transactions
        self.signed_transactions = [None for _ in self.transactions]

    def __add__(self, other):
        return TransactionGroup(self.transactions + other.transactions)

    def length(self):
        return len(self.transactions)

    def sign_with_private_keys(self, private_keys):
        if len(private_keys) == 1:
            for i, txn in enumerate(self.transactions):
                self.signed_transactions[i] = txn.sign(private_keys[0])
        else:
            for i, txn in enumerate(self.transactions):
                self.signed_transactions[i] = txn.sign(private_keys[i])

        
    def submit(self, algod, wait=False):
        try:
            txid = algod.send_transactions(self.signed_transactions)
        except AlgodHTTPError as e:
            raise Exception(str(e))
        if wait:
            return wait_for_confirmation(algod, txid)
        return {'txid': txid}