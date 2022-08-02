from .staking_config import STAKING_STRINGS

class UserStakingState:
    def __init__(self, user_local_state, staking):
        self.totalStaked = user_local_state.get(STAKING_STRINGS.user_total_staked, 0)
        self.scaledTotalStaked = user_local_state.get(STAKING_STRINGS.scaled_total_staked, 0)
        self.boostMultiplier = user_local_state.get(STAKING_STRINGS.boost_multiplier, 0)
        self.userRewardsProgramStates = {}
        print("user staking state created!")

