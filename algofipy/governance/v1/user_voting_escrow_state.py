
# IMPORTS


# INTERFACE
from algofipy.governance.v1.governance_config import VOTING_ESCROW_STRINGS

class UserVotingEscrowState:

    def __init__(self, user_local_state):
        """Constructor for the user voting escrow class.

        :param user_local_state: a dictionary representing a user's local state with
        the voting escrow contract.
        :type user_local_state: dict
        """

        self.amount_locked = user_local_state[VOTING_ESCROW_STRINGS.user_amount_locked]
        self.lock_start_time = user_local_state[VOTING_ESCROW_STRINGS.user_lock_start_time]
        self.lock_duration = user_local_state[VOTING_ESCROW_STRINGS.user_lock_duration]
        self.amount_vebank = user_local_state[VOTING_ESCROW_STRINGS.user_amount_vebank]
        self.boost_multiplier = user_local_state[VOTING_ESCROW_STRINGS.user_boost_multiplier]