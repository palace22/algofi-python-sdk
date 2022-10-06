
# IMPORTS


# INTERFACE

class RewardsManager:

    def __init__(self, governance_client, governance_config):
        """Constructor for the rewards manager object.

        :param governance_client: a governance client
        :type governance_client: :class:`GovernanceClient`
        :param governance_config: a governance config
        :type governance_config: :class:`GovernanceConfig`
        """

        self.governance_client = governance_client
        self.algod = self.governance_client.algod
        self.indexer = self.governance_client.indexer
        self.app_id = governance_config.rewards_manager_app_id