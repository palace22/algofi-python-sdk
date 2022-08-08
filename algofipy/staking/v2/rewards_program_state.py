from .staking_config import STAKING_STRINGS
from base64 import b64decode


class RewardsProgramState:

    def __init__(self, staking, staking_state, rewards_program_index):
        self.staking = staking
        self.rewards_program_index = rewards_program_index
        self.rewards_program_counter = staking_state[STAKING_STRINGS.rewards_program_counter_prefix + str(self.rewards_program_index)]
        self.rewards_asset_id = staking_state[STAKING_STRINGS.rewards_asset_id_prefix + str(self.rewards_program_index)]
        self.rewards_per_second = staking_state[STAKING_STRINGS.rewards_per_second_prefix + str(self.rewards_program_index)]
        self.rewards_issued = staking_state[STAKING_STRINGS.rewards_issued_prefix + str(self.rewards_program_index)]
        self.rewards_payed = staking_state[STAKING_STRINGS.rewards_payed_prefix + str(self.rewards_program_index)]

        non_formatted_rewards_coefficient = staking_state[STAKING_STRINGS.rewards_coefficient_prefix + str(self.rewards_program_index)]
        self.rewards_coefficient = int.from_bytes(b64decode(non_formatted_rewards_coefficient), "big")

class UserRewardsProgramState:

    def __init__(self, formatted_user_local_state, rewards_program_index, staking, user_scaled_total_staked):
        self.staking = staking
        self.rewards_program_index = rewards_program_index
        self.user_rewards_program_counter = formatted_user_local_state[STAKING_STRINGS.user_rewards_coefficient_prefix + str(self.rewards_program_index)]
        self.user_unclaimed_rewards = formatted_user_local_state[STAKING_STRINGS.user_rewards_coefficient_prefix + str(self.rewards_program_index)]

        non_formatted_rewards_coefficient = formatted_user_local_state[STAKING_STRINGS.user_rewards_coefficient_prefix + str(self.rewards_program_index)]
        self.rewards_coefficient = int.from_bytes(b64decode(non_formatted_rewards_coefficient), "big")