from .staking_config import STAKING_STRINGS


class RewardsProgramState:

    def __init__(self, staking, staking_state, rewards_program_index):
        self.staking = staking
        self.rewards_program_index = rewards_program_index
        self.rewards_program_counter = staking_state[STAKING_STRINGS.rewards_program_counter_prefix + str(self.rewards_program_index)]
        self.rewards_asset_id = staking_state[STAKING_STRINGS.rewards_asset_id_prefix + str(self.rewards_program_index)]
        self.rewards_issued = staking_state[STAKING_STRINGS.rewards_issued_prefix + str(self.rewards_program_index)]
        self.rewards_payed = staking_state[STAKING_STRINGS.rewards_payed_prefix + str(self.rewards_program_index)]

        # need to do rewards coefficient and project rewards coefficient









