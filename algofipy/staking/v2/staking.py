from algosdk import logic
from algosdk.encoding import encode_address
from algosdk.future.transaction import ApplicationNoOpTxn, ApplicationOptInTxn, ApplicationCloseOutTxn
from ...state_utils import get_global_state, format_prefix_state
from ...transaction_utils import TransactionGroup, get_default_params, get_payment_txn
from ...utils import int_to_bytes, bytes_to_int
from .staking_config import STAKING_STRINGS
from .rewards_program_state import RewardsProgramState
from base64 import b64decode
import pprint

class Staking:
    def __init__(self, staking_client, rewards_manager_app_id, staking_config):
        """The python representation of an algofi staking smart contract

        :param staking_client:
        :type staking_client: :class:`StakingClient`
        :param rewards_manager_app_id:
        :type rewards_manager_app_id: int
        :param staking_config: staking config with staking metadata
        :type staking_config: :class:`StakingConfig`
        """

        self.staking_client = staking_client
        self.algod = self.staking_client.algod
        self.indexer = self.staking_client.indexer
        self.historical_indexer = self.staking_client.historical_indexer
        self.staking_client = staking_client
        self.name = staking_config.name
        self.app_id = staking_config.app_id
        self.address = logic.get_application_address(self.app_id)
        self.asset_id = staking_config.asset_id
        self.rewards_manager_app_id = rewards_manager_app_id

    def load_state(self, block=None):
        """
        Loads staking state from the blockchain

        :param block: block at which to query staking state
        :type block: int, optional
        :rtype: None
        """

        indexer = self.historical_indexer if block else self.indexer
        global_state = get_global_state(indexer, self.app_id, block=block)

        self.latest_time = global_state[STAKING_STRINGS.latest_time]
        self.rewards_escrow_account = encode_address(b64decode(state.get(STAKING_STRINGS.rewards_escrow_account, '')))
        self.voting_escrow_app_id = global_state[STAKING_STRINGS.voting_escrow_app_id]
        self.total_staked = global_state[STAKING_STRINGS.total_staked]
        self.scaled_total_staked = global_state[STAKING_STRINGS.scaled_total_staked]
        self.rewards_manager_app_id = global_state[STAKING_STRINGS.rewards_manager_app_id]
        self.rewards_program_count = global_state[STAKING_STRINGS.rewards_program_count]
        self.rewards_program_states = {}

        formatted_state = format_prefix_state(global_state)

        for i in range(self.rewards_program_count):
            self.rewards_program_states[i] = RewardsProgramState(self, formatted_state, i)

    def get_total_staked(self):
        """Returns the total staked amount.

        :return: Staked amount in base unit terms
        :rtype: int
        """

        return self.total_staked

    def get_user_opt_in_txns(self, user, params=None):
        """Returns a :class:`TransactionGroup` object representing a staking opt in
        transaction against the algofi protocol.

        :param user: staking account for the sender
        :type user: :class:`StakingUser`
        :return: :class:`TransactionGroup` object representing an opt in group transaction of size 1
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        txn0 = ApplicationOptInTxn(user.address, params, self.app_id)

        return TransactionGroup([txn0])

    def get_user_close_out_txns(self, user, params=None):
        """Returns a :class:`TransactionGroup` object representing a staking close out
        transaction against the algofi protocol.

        :param user: staking account for the sender
        :type user: :class:`StakingUser`
        :return: :class:`TransactionGroup` object representing an opt in group transaction of size 1
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        app_args0 = [int_to_bytes(0)] # don't ignore unclaimed rewards
        txn0 = ApplicationCloseOutTxn(user.address, params, self.app_id, app_args0)

        return TransactionGroup([txn0])

    def get_stake_txns(self, user, b_asset_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing a stake group
        transaction against the algofi protocol. Sender adds bank asset amount to staking
        contract by sending them to the account address of the staking application.

        :param user: staking account for the sender
        :type user: :class:`StakingUser`
        :param b_asset_amount: amount of bank asset to add to collateral
        :type b_asset_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an opt in group transaction of size 3
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # farm ops
        app_args0 = [bytes(STAKING_STRINGS.farm_ops, "utf-8")]
        txn0 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args0)

        # sending staking asset
        txn1 = get_payment_txn(user.address, params, self.address, b_asset_amount, self.asset_id)

        # stake
        params.fee = 2000
        app_args2 = [bytes(STAKING_STRINGS.stake, "utf-8")]
        foreign_apps2 = [self.voting_escrow_app_id or 1]
        txn2 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args2, foreign_apps=foreign_apps2)

        return TransactionGroup([txn0, txn1, txn2])

    def get_unstake_txns(self, user, b_asset_amount, params=None):
        """Returns a :class:`TransactionGroup` object representing a unstake group
        transaction against the algofi protocol. Sender reclaims bank asset by unstaking.

        :param user: staking account for the sender
        :type user: :class:`StakingUser`
        :param b_asset_amount: amount of bank asset to add to collateral
        :type b_asset_amount: int
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing an opt in group transaction of size 2
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        # farm ops
        app_args0 = [bytes(STAKING_STRINGS.farm_ops, "utf-8")]
        txn0 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args0)

        # unstake
        params.fee = 3000
        app_args1 = [bytes(STAKING_STRINGS.unstake, "utf-8"), int_to_bytes(b_asset_amount)]
        foreign_apps1 = [self.voting_escrow_app_id or 1]
        foreign_assets1 = [self.asset_id]
        txn1 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args1, foreign_apps=foreign_apps1, foreign_assets=foreign_assets1)

        return TransactionGroup([txn0, txn1])

    def get_claim_txns(self, user, params=None):
        """Returns a :class:`TransactionGroup` object representing a claim rewards group
        transaction against the algofi protocol. Sender claims accrued rewards from all rewards program.

        :param user: account for the sender
        :type user: :class:`StakingUser`
        :param params: algod params
        :type params: :class: `algosdk.future.transaction.SuggestedParams`
        :return: :class:`TransactionGroup` object representing a claim rewards group transaction.
        :rtype: :class:`TransactionGroup`
        """

        if params is None:
            params = get_default_params(self.algod)

        txns = []

        for i in range(self.rewards_program_count):
            if user.user_staking_states[self.app_id].user_rewards_program_states[i].user_unclaimed_rewards > 0:
                # farm ops
                params.fee = 1000
                app_args0 = [bytes(STAKING_STRINGS.farm_ops, "utf-8")]
                txn0 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args0)

                # claim rewards
                params.fee = 3000
                app_args1 = [bytes(STAKING_STRINGS.claim_rewards, "utf-8"), int_to_bytes(i)]
                accounts1 = [self.rewards_escrow_account]
                foreign_apps1 = [self.voting_escrow_app_id or 1]
                foreign_assets1 = [self.rewards_program_states[i].rewards_asset_id]
                txn1 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args1, accounts=accounts1, foreign_apps=foreign_apps1, foreign_assets=foreign_assets1)

                txns.extend([txn0, txn1])

        if len(txns) == 0:
            return []
        else:
            return TransactionGroup(txns)
