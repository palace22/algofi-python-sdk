
# IMPORTS
from base64 import b64decode
from algosdk.encoding import encode_address

# INTERFACE
from algofipy.governance.v1.governance_config import ADMIN_STRINGS, PROPOSAL_STRINGS

class UserAdminState:

    def __init__(self, storage_address, user_storage_local_states, governance_client):
        """Initialize a user admin contract state.
        """

        proposal_app_ids = [proposal.proposal_app_id for proposal in governance_client.admin.proposals]
        self.storage_address = storage_address
        self.user_proposal_states = {}
        # iterate over user local states
        for app_id in user_storage_local_states:
            user_storage_local_state = user_storage_local_states[app_id]
            # admin user data
            if app_id == govenrance_client.admin.admin_app_id:
                self.open_to_delegation = user_storage_local_state.get(ADMIN_STRINGS.open_to_delegation, False)
                self.delegator_count = user_storage_local_state.get(ADMIN_STRINGS.delegator_count, 0)
                self.delegating_to = encode_address(b64decode(user_storage_local_state.get(ADMIN_STRINGS.open_to_delegation, "")))
            # proposal user data
            if app_id in proposal_app_ids:
                self.user_proposal_states[app_id] = UserProposalState(user_storage_local_state)

class UserProposalState:

    def __init__(self, storage_proposal_local_state):
        """Initiialize user proposal state.
        """

        self.for_or_against = storage_proposal_local_state[PROPOSAL_STRINGS.for_or_against]
        self.voting_amount = storage_proposal_local_state[PROPOSAL_STRINGS.voting_amount]