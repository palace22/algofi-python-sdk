from .staking_config import STAKING_CONFIGS, rewards_manager_app_id
from ...state_utils import get_local_states 
from .staking import Staking
from .user_staking_state import UserStakingState
import pprint

class StakingUser:
  def __init__(self, staking_client, address):
    self.staking_client = staking_client
    self.algod = self.staking_client.algod
    self.indexer = self.staking_client.indexer
    self.historical_indexer = self.staking_client.historical_indexer
    self.address = address

  def load_state(self, block=None):
    # staking configs
    staking_configs = STAKING_CONFIGS[self.staking_client.network]
    # app ids for staking contracts
    all_staking_contracts = [config.app_id for config in staking_configs]

    # get opted in staking contracts
    self.opted_in_staking_contracts = []
    self.user_staking_states = {}

    # get local states
    indexer = self.historical_indexer if block else self.indexer
    local_states = get_local_states(indexer, self.address, block=block)

    for app_id, local_state in local_states.items():
      if int(app_id) in all_staking_contracts:
        staking_config = list(filter(lambda config: config.app_id == int(app_id), STAKING_CONFIGS[self.staking_client.network]))[0]
        staking = Staking(self.staking_client, rewards_manager_app_id[self.staking_client.network], staking_config)
        staking.load_state(block=block)
        self.user_staking_states[app_id] = UserStakingState(local_state, staking)
        self.opted_in_staking_contracts.append(app_id)