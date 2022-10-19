from .staking_config import STAKING_STRINGS
from .rewards_program_state import UserRewardsProgramState
from ...state_utils import format_prefix_state

class UserStakingState:
    def __init__(self, user_local_state, staking):
        self.total_staked = user_local_state.get(STAKING_STRINGS.user_total_staked, 0)
        self.scaled_total_staked = user_local_state.get(STAKING_STRINGS.scaled_total_staked, 0)
        self.boost_multiplier = user_local_state.get(STAKING_STRINGS.boost_multiplier, 0)
        self.user_rewards_program_states = {}
        rewards_program_count = staking.rewards_program_count

        for i in range(rewards_program_count):
            self.user_rewards_program_states[i] = UserRewardsProgramState(
                user_local_state,
                format_prefix_state(user_local_state),
                i,
                staking,
                self.scaled_total_staked
            )