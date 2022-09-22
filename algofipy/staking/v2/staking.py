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
        indexer = self.historical_indexer if block else self.indexer
        global_state = get_global_state(indexer, self.app_id, block=block)

        self.latest_time = global_state[STAKING_STRINGS.latest_time]
        # TODO: Do this need a "encode_address(b64decode" like market.py does?
        self.rewards_escrow_account = global_state[STAKING_STRINGS.rewards_escrow_account]
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
        # TODO: Is this correct?
        return self.total_staked

    def get_user_opt_in_txns(self, user):
        if params is None:
            params = get_default_params(self.algod)

        txn0 = ApplicationOptInTxn(user.address, params, self.app_id)

        return TransactionGroup([txn0])

    def get_user_close_out_txns(self, user):
        if params is None:
            params = get_default_params(self.algod)

        app_args0 = [int_to_bytes(0)] # don't ignore unclaimed rewards
        txn0 = ApplicationCloseOutTxn(user.address, params, self.app_id, app_args0)

        return TransactionGroup([txn0])

    def get_stake_txns(self, user, amount, params=None):
        if params is None:
            params = get_default_params(self.algod)

        # farm ops
        app_args0 = [bytes(STAKING_STRINGS.farm_ops, "utf-8")]
        txn0 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args0)

        # sending staking asset
        txn1 = get_payment_txn(user.address, params, self.address, amount, self.asset_id)

        # stake
        params.fee = 2000
        app_args2 = [bytes(STAKING_STRINGS.stake, "utf-8")]
        foreign_apps2 = [self.voting_escrow_app_id or 1]
        txn2 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args2, foreign_apps=foreign_apps2)

        return TransactionGroup([txn0, txn1, txn2])

    def get_unstake_txns(self, user, amount, params=None):
        if params is None:
            params = get_default_params(self.algod)

        # farm ops
        app_args0 = [bytes(STAKING_STRINGS.farm_ops, "utf-8")]
        txn0 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args0)

        # unstake
        params.fee = 3000
        app_args1 = [bytes(STAKING_STRINGS.unstake, "utf-8"), int_to_bytes(amount)]
        foreign_apps1 = [self.voting_escrow_app_id or 1]
        foreign_assets1 = [self.asset_id]
        txn1 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args1, foreign_apps=foreign_apps1, foreign_assets=foreign_assets1)

        return TransactionGroup([txn0, txn1])

    def get_claim_txns(self, user):
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
