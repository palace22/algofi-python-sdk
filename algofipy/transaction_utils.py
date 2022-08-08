# IMPORTS

# external
from algosdk.error import AlgodHTTPError
from algosdk.v2client.algod import AlgodClient

# local
from algosdk.future.transaction import assign_group_id, PaymentTxn, AssetTransferTxn, LogicSig, LogicSigTransaction

from .globals import ALGO_ASSET_ID

# FUNCTIONS

def get_default_params():
    """Get default params for an Algorand transaction with fee = 1000, flat_fee = True.

    :param algod: Algorand algod client
    :type algod: :class:`AlgodClient`
    :return: suggested params object
    :rtype: class:`SuggestedParams`
    """

    params = algod.suggested_params()
    params.flat_fee = True
    params.fee = 1000
    return params

def get_payment_txn(sender, params, receiver, amount, asset_id):
    """Get a payment transaction object.

    :param sender: sender address
    :type sender: str
    :param params: transaction params object
    :type params: :class:`SuggestedParams`
    :param receiver: receiver address
    :type receiver: str
    :param amount: amount to send in microALGOs
    :type amount: int
    :return: payment / asset transaction transaction
    :rtype: :class:`PaymentTxn` or :class:`AssetTransferTxn`
    """

    if asset_id == ALGO_ASSET_ID:
        txn = PaymentTxn(sender=sender, sp=params, receiver=receiver, amt=amount)
    else:
        txn = AssetTransferTxn(sender=sender, sp=params, receiver=receiver, amt=amount, index=asset_id)
    return txn

def wait_for_confirmation(algod, txid):
    """Wait for confirmation from network for transaction with given id.

    :param algod: Algorand algod node
    :type algod: :class:`AlgodClient`
    :param txid: transaction id
    :type txid: str
    :return: transaction information dict
    :rtype: dict
    """
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
        """Transaction group object.

        :param transactions: list of transaction objects
        :type transactions: list
        """

        for t in transactions:
            t.group = None
        transactions = assign_group_id(transactions)
        self.transactions = transactions
        self.signed_transactions = [None for _ in self.transactions]

    def __add__(self, other):
        """Add dunder method.

        :param other: other transaction group
        :type other: :class:`TransactionGroup`
        """

        return TransactionGroup(self.transactions + other.transactions)

    def length(self):
        """Get length of the transaction group.

        :return: length of transactiong group
        :rtype: int
        """

        return len(self.transactions)

    def sign_with_private_keys(self, private_keys):
        """Signs transactions in the group with provided private keys. If a singleton list is provided, signs all
        transactions with the same key, otherwise signs ith transaction with the ith key in the list

        :param private_keys: a list of signer keys
        :type private_keys: list of strings
        :return: None
        """

        if len(private_keys) == 1:
            for i, txn in enumerate(self.transactions):
                self.signed_transactions[i] = txn.sign(private_keys[0])
        else:
            for i, txn in enumerate(self.transactions):
                self.signed_transactions[i] = txn.sign(private_keys[i])

        
    def submit(self, algod, wait=False):
        """Submit algorand transaction group and optionally wait for confirmation.

        :param algod: Algorand algod client
        :type algod: :class:`AlgodClient`
        :param wait: whether to wait for transaction confirmation from network
        :type wait: bool, optional
        :return: length of transactiong group
        :rtype: int
        """

        try:
            txid = algod.send_transactions(self.signed_transactions)
        except AlgodHTTPError as e:
            raise Exception(str(e))
        if wait:
            return wait_for_confirmation(algod, txid)
        return {'txid': txid}