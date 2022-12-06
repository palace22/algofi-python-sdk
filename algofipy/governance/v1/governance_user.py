# IMPORTS
from base64 import b64decode
from algosdk.encoding import encode_address

# INTERFACE
from algofipy.state_utils import get_local_states
from algofipy.governance.v1.governance_config import ADMIN_STRINGS
from algofipy.governance.v1.user_admin_state import UserAdminState
from algofipy.governance.v1.user_voting_escrow_state import UserVotingEscrowState
from algofipy.governance.v1.user_rewards_manager_state import UserRewardsManagerState


class GovernanceUser:
    def __init__(self, governance_client, address):
        """Constructor for the governance user class.

        :param governance_client: a governance client
        :type governance_client: :class:`GovernanceClient`
        :param address: address of the user
        :type address: str
        """

        self.governance_client = governance_client
        self.algod = self.governance_client.algod
        self.indexer = self.governance_client.indexer
        self.historical_indexer = self.governance_client.historical_indexer
        self.address = address
        self.load_state()

    def load_state(self, block=None):
        """A function which will load in all of the state for a governance user
        including their admin state, voting escrow state, and rewards manager
        state into the governance user object.

        :param block: block at which to load user governance state
        :type block: int, optional
        """

        # get user local states
        indexer = self.historical_indexer if block else self.indexer
        user_local_states = get_local_states(indexer, self.address, block=block)
        self.opted_into_governance = False

        for app_id in user_local_states:
            user_local_state = user_local_states[app_id]
            # admin user local state
            if app_id == self.governance_client.admin.admin_app_id:
                storage_address = encode_address(
                    b64decode(user_local_state.get(ADMIN_STRINGS.storage_account, ""))
                )
                user_storage_local_states = get_local_states(
                    self.indexer, storage_address
                )
                self.user_admin_state = UserAdminState(
                    storage_address, user_storage_local_states, self.governance_client
                )
                self.opted_into_governance = True
            # voting escrow user local state
            if app_id == self.governance_client.voting_escrow.app_id:
                self.user_voting_escrow_state = UserVotingEscrowState(user_local_state)
            # rewards manager user local state
            if app_id == self.governance_client.rewards_manager.app_id:
                self.user_rewards_manager_state = UserRewardsManagerState()

    def voted_in_proposal(self, proposal_app_id):
        """Return a dict of information for the user vote in a proposal

        :param proposal_app_id: proposal app id for a proposal
        :type proposal_app_id: int
        :return: dict of information about the user proposal vote
        :rtype: dict
        """

        user_local_states = get_local_states(
            self.indexer, self.user_admin_state.storage_address
        )
        return user_local_states.get(proposal_app_id, {})
