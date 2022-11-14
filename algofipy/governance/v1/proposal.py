# IMPORTS
import base64
from algosdk import logic
from requests import get

# INTERFACE
from algofipy.state_utils import get_local_states, get_global_state
from algofipy.utils import base64_to_utf8
from algofipy.globals import get_analytics_endpoint
from algofipy.governance.v1.governance_config import ADMIN_STRINGS, PROPOSAL_STRINGS


class Proposal:
    def __init__(self, governance_client, proposal_app_id):
        """Constructor for the proposal class.

        :param governance_client: a governance client
        :type governance_client: :class:`GovernanceClient`
        :param proposal_app_id: proposal app id
        :type proposal_app_id: int
        """

        self.governance_client = governance_client
        self.algod = governance_client.algod
        self.indexer = governance_client.indexer
        self.app_id = proposal_app_id
        self.admin_app_id = governance_client.governance_config.admin_app_id
        self.proposal_address = logic.get_application_address(self.app_id)
        self.load_state()

    def load_state(self):
        """Function that will update the data on the proposal object with the global
        and local data of the proposal contract on chain.
        """

        # get vote state from admin contract
        proposal_local_states = get_local_states(self.indexer, self.proposal_address)
        admin_local_state = proposal_local_states.get(self.admin_app_id, {})
        if admin_local_state:
            self.votes_for = admin_local_state.get(ADMIN_STRINGS.votes_for, 0)
            self.votes_against = admin_local_state.get(ADMIN_STRINGS.votes_against, 0)
            self.vote_close_time = admin_local_state.get(
                ADMIN_STRINGS.vote_close_time, 0
            )
            self.execution_time = admin_local_state.get(ADMIN_STRINGS.execution_time, 0)
            self.executed = admin_local_state.get(ADMIN_STRINGS.executed, False)
            self.canceled_by_emergency_dao = admin_local_state.get(
                ADMIN_STRINGS.canceled_by_emergency_dao, False
            )
        else:
            raise Exception("Proposal is not opted into admin contract.")

        # get proposal metadata from proposal contract
        proposal_global_state = get_global_state(self.indexer, self.app_id)
        self.title = proposal_global_state[PROPOSAL_STRINGS.title]
        self.link = proposal_global_state[PROPOSAL_STRINGS.link]

    def get_proposal_data(topic_id):
        """Get proposal data from Algofi governance portal

        :param topic_id: topic id for proposal posted on Algofi governance portal.
        :type topic_id: int
        """

        try:
            data = get(
                get_analytics_endpoint(self.governance_client.network)
                + "/getDiscourseTopic?topic_id="
                + topic_id
            ).json()
        except:
            raise Exception("Unable to find proposal with topic_id %i)" % (topic_id))
        self.data = data
