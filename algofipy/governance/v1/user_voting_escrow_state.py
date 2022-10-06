
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

        self.amount_locked = user_local_state.get(VOTING_ESCROW_STRINGS.user_amount_locked, 0)
        self.lock_start_time = user_local_state.get(VOTING_ESCROW_STRINGS.user_lock_start_time, 0)
        self.lock_duration = user_local_state.get(VOTING_ESCROW_STRINGS.user_lock_duration, 0)
        self.amount_vebank = user_local_state.get(VOTING_ESCROW_STRINGS.user_amount_vebank, 0)
        self.boost_multiplier = user_local_state.get(VOTING_ESCROW_STRINGS.user_boost_multiplier, 0)