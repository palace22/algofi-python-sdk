# IMPORTS

# external
from algosdk.error import AlgodHTTPError
from algosdk.v2client.algod import AlgodClient

# local
from algosdk.future.transaction import (
    assign_group_id,
    PaymentTxn,
    AssetTransferTxn,
    LogicSig,
    LogicSigTransaction,
)

from .globals import ALGO_ASSET_ID

# FUNCTIONS


def get_default_params(algod):
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


def get_payment_txn(sender, params, receiver, amount, asset_id=ALGO_ASSET_ID):
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
        txn = AssetTransferTxn(
            sender=sender, sp=params, receiver=receiver, amt=amount, index=asset_id
        )
    return txn

def create_asset_transaction(
    algod,
    sender,
    total,
    decimals,
    default_frozen,
    manager,
    reserve,
    freeze,
    clawback,
    unit_name,
    asset_name,
    url,
):
    """Get an asset creation txn object.

    :param algod: algod client
    :type algod: :class:`AlgodClient`
    :param sender: sender
    :type sender: str
    :param total: total amount of asset in base units
    :type total: int
    :param decimals: number of decimals for asset
    :type decimals: int
    :param default_frozen: asset is defaulted to frozen on launch
    :type default_frozen: boolean
    :param manager: manager address
    :type manager: str
    :param reserve: reserve address
    :type reserve: str
    :param freeze: freeze address
    :type freeze: str
    :param unit_name: unit name
    :type unit_name: str
    :param asset_name: asset name
    :type asset_name: str
    :param url: url for asset
    :type url: str
    :return: asset creation transaction object
    :rtype: :class:`AssetCreateTxn`
    """

    params = get_default_params(algod)

    return AssetCreateTxn(
        sender=sender,
        sp=params,
        total=total,
        decimals=decimals,
        default_frozen=default_frozen,
        manager=manager,
        reserve=reserve,
        freeze=freeze,
        clawback=clawback,
        unit_name=unit_name,
        asset_name=asset_name,
        url=url,
    )


def wait_for_confirmation(algod, txid):
    """Wait for confirmation from network for transaction with given id.

    :param algod: Algorand algod node
    :type algod: :class:`AlgodClient`
    :param txid: transaction id
    :type txid: str
    :return: transaction information dict
    :rtype: dict
    """

    last_round = algod.status().get("last-round")
    txinfo = algod.pending_transaction_info(txid)
    while not (txinfo.get("confirmed-round") and txinfo.get("confirmed-round") > 0):
        print("Waiting for confirmation")
        last_round += 1
        algod.status_after_block(last_round)
        txinfo = algod.pending_transaction_info(txid)
    txinfo["txid"] = txid
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

    def sign_with_private_key(self, private_key):
        """Signs the transactions with specified private key and saves to class state
        :param private_key: private key of user
        :type private_key: string
        """

        for i, txn in enumerate(self.transactions):
            self.signed_transactions[i] = txn.sign(private_key)

    def sign_with_private_keys(self, private_keys, is_logic_sig=None):
        """Signs the transactions with specified private key and saves to class state
        :param private_keys: private key of user
        :type private_keys: string
        :param is_logic_sig: if given "pkey" is a logicsig
        :type is_logic_sig: list
        """

        if not is_logic_sig:
            is_logic_sig = [False] * len(private_keys)

        assert len(private_keys) == len(self.transactions)
        assert len(private_keys) == len(is_logic_sig)
        for i, txn in enumerate(self.transactions):
            if is_logic_sig[i]:
                self.signed_transactions[i] = LogicSigTransaction(txn, private_keys[i])
            else:
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
        return {"txid": txid}
