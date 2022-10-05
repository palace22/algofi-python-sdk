
# IMPORTS


# INTERFACE

class RewardsManager:

    def __init__(self, governance_client, governance_config):
        """Initialize the rewards manager contract.
        """

        self.governance_client = governance_client
        self.algod = self.governance_client.algod
        self.indexer = self.governance_client.indexer
        self.app_id = governance_config.rewards_manager_app_id