from .staking_config import STAKING_CONFIGS, rewards_manager_app_id, STAKING_STRINGS
from .staking import Staking
from .staking_user import StakingUser

class StakingClient: 

    def __init__(self, algofi_client):
        self.algofi_client = algofi_client
        self.algod = self.algofi_client.algod
        self.indexer = self.algofi_client.indexer
        self.historical_indexer = self.algofi_client.historical_indexer
        self.network = self.algofi_client.network
        self.historical_indexer = self.algofi_client.historical_indexer
        self.staking_configs = STAKING_CONFIGS[self.network]

        self.staking_contracts = {}
        self.load_state()
        
    def load_state(self):
        for staking_config in self.staking_configs:
            self.staking_contracts[staking_config.app_id] = Staking(self, rewards_manager_app_id[self.network], staking_config)
            self.staking_contracts[staking_config.app_id].load_state()

    def get_user(self, address):
        return StakingUser(self, address)

    def get_staking_state(self, staking_app_id):
        """Function that uses indexer to query for users' staking state
        """

        # query all users opted into admin contract
        next_page = ""
        staking_accounts = []
        while next_page != None:
            users = self.indexer.accounts(next_page=next_page, limit=1000, application_id=staking_app_id, exclude="assets,created-apps,created-assets")
            if len(users.get("accounts",[])):
                staking_accounts.extend(users["accounts"])
            if users.get("next-token", None):
                next_page = users["next-token"]
            else:
                next_page = None

        # filter to accounts with relevant key
        user_data = {}
        for user in staking_accounts:
            user_local_state = user.get("apps-local-state", {})
            for app_local_state in user_local_state:
                if app_local_state["id"] == staking_app_id:
                    formatted_state = format_state(app_local_state.get("key-value", []))
                    boost_multiplier = formatted_state.get(STAKING_STRINGS.boost_multiplier, 0)
                    user_data[user["address"]] = {
                        "boost_multiplier": boost_multiplier
                    }
        return user_data