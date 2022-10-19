
# IMPORTS
from algosdk.future.transaction import ApplicationNoOpTxn, AssetTransferTxn
from algosdk import logic
import time

# INTERFACE
from algofipy.state_utils import get_global_state
from algofipy.utils import int_to_bytes
from algofipy.governance.v1.governance_config import VOTING_ESCROW_STRINGS
from algofipy.transaction_utils import TransactionGroup, get_default_params

class VotingEscrow:

    def __init__(self, governance_client):
        """The constructor for the voting escrow object.
        """

        self.governance_client = governance_client
        self.algod = self.governance_client.algod
        self.indexer = self.governance_client.indexer
        self.app_id = self.governance_client.governance_config.voting_escrow_app_id
        self.governance_token = self.governance_client.governance_config.governance_token
        self.voting_escrow_min_time_lock_seconds = governance_client.governance_config.voting_escrow_min_time_lock_seconds
        self.voting_escrow_max_time_lock_seconds = governance_client.governance_config.voting_escrow_max_time_lock_seconds
        self.load_state()

    def load_state(self):
        """Function which will update the data on the voting escrow object to match
        that of the global state of the voting escrow contract.
        """

        global_state = get_global_state(self.indexer, self.app_id)
        self.total_locked = global_state.get(VOTING_ESCROW_STRINGS.total_locked, 0)
        self.total_vebank = global_state.get(VOTING_ESCROW_STRINGS.total_vebank, 0)
        self.asset_id = global_state.get(VOTING_ESCROW_STRINGS.asset_id, 0)

    def get_update_vebank_data_txns(self, user_calling, user_updating):
        """Constructs a series of transactions to update a target user's vebank.

        :param user_calling: algofi user object for user updating
        :type user_calling: :class:`AlgofiUser`
        :param user_updating: algofi user object for user being updated
        :type user_updating: :class:`AlgofiUser`
        :return: transaction group for updating target user vebank amount
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = ApplicationNoOpTxn(
            sender=user_calling.address,
            sp=params,
            index=self.app_id,
            app_args=[bytes(VOTING_ESCROW_STRINGS.update_vebank_data, "utf-8")],
            accounts=[user_updating.address]
        )

        return TransactionGroup([txn0])

    def get_lock_txns(self, user, amount, duration_seconds):
        """Constructs a series of transactions that lock a user's BANK.

        :param user: user who is locking
        :type user: :class:`AlgofiUser`
        :param amount: amount they are locking in microBANK
        :type amount: int
        :param duration_seconds: amount of time they are locking for in seconds
        :type duration_seconds: int
        :return: transaction group for locking BANK
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)
        
        txn0 = AssetTransferTxn(
            sender=user.address,
            sp=params,
            receiver=logic.get_application_address(self.app_id),
            amt=amount,
            index=self.governance_token
        )

        txn1 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.app_id,
            app_args=[bytes(VOTING_ESCROW_STRINGS.lock, "utf-8"), int_to_bytes(duration_seconds)],
        )

        return TransactionGroup([txn0, txn1])

    def get_extend_lock_txns(self, user, duration_seconds):
        """Constructs a series of transactions that extend a user's lock.

        :param user: user who is locking
        :type user: :class:`AlgofiUser`
        :param duration_seconds: amount of time they are extending for in seconds
        :type duration_seconds: int
        :return: transaction group for extending lock of a user
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.app_id,
            app_args=[bytes(VOTING_ESCROW_STRINGS.extend_lock, "utf-8"), int_to_bytes(duration_seconds)],
        )

        return TransactionGroup([txn0])

    def get_increase_lock_amount_txns(self, user, amount):
        """Constructs a series of transactions that increase a user's lock amount.

        :param user: user who is locking
        :type user: :class:`AlgofiUser`
        :param amount: amount they are increasing their lock for in microBANK
        :type amount: int
        :return: transaction group for increasing the locked amount
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = AssetTransferTxn(
            sender=user.address,
            sp=params,
            receiver=logic.get_application_address(self.app_id),
            amt=amount,
            index=self.governance_token
        )

        txn1 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.app_id,
            app_args=[bytes(VOTING_ESCROW_STRINGS.increase_lock_amount, "utf-8")]
        )

        return TransactionGroup([txn0, txn1])

    def get_claim_txns(self, user):
        """Constructs a series of transactions for claiming the user's locked amount after the timelock expires.

        :param user: user who is claiming locked amount
        :type user: :class:`AlgofiUser`
        :return: transaction group for claiming the user's locked amount
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)
        
        params.fee = 2000
        txn0 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.app_id,
            app_args=[bytes(VOTING_ESCROW_STRINGS.claim, "utf-8")],
            foreign_assets=[self.governance_token]
        )

        return TransactionGroup([txn0])
    
    def get_projected_vebank_amount(self, user_voting_escrow_state):
        """Get projected vebank amount for user.

        :param user_voting_escrow_state: user voting escrow state
        :type user_voting_escrow_state: :class:`UserVotingEscrowState`
        :return: projected vebank amount
        :rtype: int
        """

        current_time = int(time.time())
        lock_end_time = user_voting_escrow_state.lock_start_time + user_voting_escrow_state.lock_duration
        time_remaining = lock_end_time - current_time
        amount_locked = user_voting_escrow_state.amount_locked
        if time_remaining <= 0 or amount_locked == 0:
            return 0
        else:
            return int((amount_locked * time_remaining) // (365 * 24 * 60 * 60))
    
    def get_projected_boost_multiplier(self, user_voting_escrow_state):
        """Get projected vebank amount for user.

        :param user_voting_escrow_state: user voting escrow state
        :type user_voting_escrow_state: :class:`UserVotingEscrowState`
        :return: projected vebank amount
        :rtype: int
        """

        projected_vebank = self.get_projected_vebank_amount(user_voting_escrow_state)
        if self.total_vebank > 0:
            return int((projected_vebank * 1e12) // self.total_vebank)
        else:
            return 0