
# IMPORTS
from base64 import b64decode
from algosdk.encoding import encode_address

# INTERFACE
from algofipy.state_utils import get_local_states
from algofipy.governance.v1.user_admin_state import UserAdminState
from algofipy.governance.v1.user_voting_escrow_state import UserVotingEscrowState
from algofipy.governance.v1.user_rewards_manager_state import UserRewardsManagerState

class GovernanceUser:

    def __init__(self, governance_client, address):
        """Initialize Algofi governance user.
        """

        self.governance_client = governance_client
        self.algod = self.governance_client.algod
        self.indexer = self.governance_client.indexer
        self.address = address

    def load_state(self, user_local_states):
        """Load state for governance user.

        :param user_local_states: dict mapping app ids to local state dicts of user
        :type user_local_states: dict
        """

        for app_id in user_local_states:
            user_local_state = user_local_states[app_id]
            # admin user local state
            if app_id == self.governance_client.admin.admin_app_id:
                storage_address = encode_address(b64decode(user_local_state.get(ADMIN_STRINGS.storage_account, "")))
                user_storage_local_states = get_local_states(self.indexer, storage_address)
                self.user_admin_state = UserAdminState(storage_address, user_storage_local_states, self.governance_client)
                self.opted_into_governance = True
            # voting escrow user local state
            if app_id == self.governance_client.voting_escrow.app_id:
                self.user_voting_escrow_state = UserVotingEscrowState(user_local_state)
            # rewards manager user local state
            if app_id == self.governance_client.rewards_manager.app_id:
                self.user_rewards_manager_state = UserRewardsManagerState()