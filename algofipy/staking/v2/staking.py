from algosdk import logic
from ...state_utils import get_global_state
from .staking_config import STAKING_STRINGS
from .rewards_program_state import RewardsProgramState
from base64 import b64decode
import pprint


def format_prefix_state(state):
    formatted_state = {}
    for key, value in state.items():
        try:
            index_of_underscore = key.index("_")
        except:
            index_of_underscore = -1
        # if the prefix actually exist
        if index_of_underscore > 0:
            prefix = key[0: index_of_underscore + 1]
            raw_bytes = bytes(key[index_of_underscore + 1:], "utf-8")
            formatted = int.from_bytes(raw_bytes, "big")
            formatted_state[prefix + str(formatted)] = value
    print(formatted_state)
    return formatted_state

class Staking:
    def __init__(self, algod, staking_client, rewards_manager_app_id, staking_config):
        self.algod = algod
        self.staking_client = staking_client
        self.name = staking_config.name
        self.app_id = staking_config.app_id
        self.address = logic.get_application_address(self.app_id)
        self.asset_id = staking_config.asset_id
        self.rewards_manager_app_id = rewards_manager_app_id
    
    def load_state(self):
        global_state = get_global_state(self.staking_client.algofi_client.indexer, self.app_id)

        self.latest_time = global_state[STAKING_STRINGS.latest_time]
        self.rewards_escrow_account = global_state[STAKING_STRINGS.rewards_escrow_account]
        self.voting_escrow_app_id = global_state[STAKING_STRINGS.voting_escrow_app_id]
        self.total_staked = global_state[STAKING_STRINGS.total_staked]
        self.scaled_total_staked = global_state[STAKING_STRINGS.scaled_total_staked]
        self.rewards_manager_app_id = global_state[STAKING_STRINGS.rewards_manager_app_id]
        self.rewards_program_count = global_state[STAKING_STRINGS.rewards_program_count]
        self.rewards_program_states = {}

        formatted_state = format_prefix_state(global_state)
        pprint.pprint(formatted_state)
        breakpoint()


        for i in range(self.rewards_program_count):
            this.rewards_program_states[i] = RewardsProgramState(self, formatted_state, i)

