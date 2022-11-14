# IMPORTS

# external
from algosdk.future.transaction import *

from algosdk.logic import get_application_address

# local
from .lending_config import MANAGER_MIN_BALANCE, MANAGER_STRINGS
from .manager_config import ManagerConfig

# INTERFACE
from ...globals import ALGO_ASSET_ID
from ...transaction_utils import get_default_params, get_payment_txn, TransactionGroup
from ...utils import int_to_bytes


class Manager:
    def __init__(self, lending_client, manager_config):
        """An object that encapsulates algofi lending manager contract

        :param lending_client: a client for interacting with the algofi lending protocol
        :type lending_client: :class:`LendingClient`
        :param manager_config: an object that stores the smart contract metadata
        :type manager_config: :class:`ManagerConfig`
        """

        self.lending_client = lending_client
        self.algod = self.lending_client.algod
        self.indexer = self.lending_client.indexer
        self.app_id = manager_config.app_id
        self.address = get_application_address(self.app_id)

    # TRANSACTION BUILDERS

    def get_opt_in_txns(self, user, storage_address, params=None):
        """Returns a :class:`TransactionGroup` object representing a lending manager opt in
        transaction against the algofi protocol. The second transaction should be signed by the key of the storage
        address.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param storage_address: address created owned by the user, to be rekeyed to the manager
        :type storage_address: str
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an opt in group transaction of size 3
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # fund storage account
        txn0 = get_payment_txn(
            user.address, params, storage_address, MANAGER_MIN_BALANCE, ALGO_ASSET_ID
        )

        # storage account opt in and rekey
        app_args1 = [bytes(MANAGER_STRINGS.storage_account_opt_in, "utf-8")]
        txn1 = ApplicationOptInTxn(
            storage_address,
            params,
            self.app_id,
            app_args1,
            rekey_to=get_application_address(self.app_id),
        )

        # user opt in
        app_args2 = [bytes(MANAGER_STRINGS.user_opt_in, "utf-8")]
        accounts2 = [storage_address]
        txn2 = ApplicationOptInTxn(
            user.address, params, self.app_id, app_args2, accounts=accounts2
        )

        return TransactionGroup([txn0, txn1, txn2])

    def get_close_out_txns(self, user, params=None):
        """Returns a :class:`TransactionGroup` object representing a lending manager close out
        transaction against the algofi protocol. The manager will close the storage account and return funds to the
        user. This transaction will fail unless the user has nothing borrowed and no active collateral

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an close out group transaction of size 1
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # close out of manager
        params.fee = 2000
        accounts0 = [user.storage_address]
        txn0 = ApplicationCloseOutTxn(
            user.address, params, self.app_id, accounts=accounts0
        )

        # add clear state txn
        params.fee = 1000
        txn1 = ApplicationClearStateTxn(user.storage_address, params, self.app_id)

        # pay algos on stoarge account to user
        params.fee = 1000
        txn2 = PaymentTxn(
            user.storage_address,
            params,
            user.address,
            int(0),
            close_remainder_to=user.address,
        )

        return TransactionGroup([txn0, txn1, txn2])

    def get_market_opt_in_txns(self, user, market, params=None):
        """Returns a :class:`TransactionGroup` object representing a lending market opt in
        transaction against the algofi protocol.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param market: market to opt in to
        :type market: :class:`LendingMarket`
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an opt in group transaction of size 3
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # fund storage account
        txn0 = get_payment_txn(
            user.address,
            params,
            user.storage_address,
            market.local_min_balance,
            ALGO_ASSET_ID,
        )

        # validate market
        app_args1 = [bytes(MANAGER_STRINGS.validate_market, "utf-8")]
        accounts1 = [market.address]
        foreign_apps1 = [market.app_id]
        txn1 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args1,
            accounts=accounts1,
            foreign_apps=foreign_apps1,
        )

        # opt into market
        params.fee = 2000
        app_args2 = [bytes(MANAGER_STRINGS.user_market_opt_in, "utf-8")]
        accounts2 = [user.storage_address]
        foreign_apps2 = [market.app_id]
        txn2 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args2,
            accounts=accounts2,
            foreign_apps=foreign_apps2,
        )

        return TransactionGroup([txn0, txn1, txn2])

    def get_market_close_out_txns(self, user, market, params=None):
        """Returns a :class:`TransactionGroup` object representing a lending market close out
        transaction against the algofi protocol.

        :param user: account for the sender
        :type user: :class:`LendingUser`
        :param market: market to opt in to
        :type market: :class:`LendingMarket`
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an close out group transaction of size 1
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        page, offset = user.get_market_page_offset(market.app_id)

        # close out of market
        params.fee = 3000
        app_args0 = [
            bytes(MANAGER_STRINGS.user_market_close_out, "utf-8"),
            int_to_bytes(page) + int_to_bytes(offset),
        ]
        accounts0 = [user.storage_address]
        foreign_apps0 = [market.app_id]
        txn0 = ApplicationNoOpTxn(
            user.address,
            params,
            self.app_id,
            app_args0,
            accounts=accounts0,
            foreign_apps=foreign_apps0,
        )

        return TransactionGroup([txn0])
