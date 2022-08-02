from .staking_config import STAKING_CONFIGS
from ...state_utils import get_local_states 
from .staking import Staking
from .user_staking_state import UserStakingState
import pprint

class StakingUser:
  def __init__(self, staking_client, address):
    self.staking_client = staking_client
    self.algod = self.staking_client.algod
    self.address = address

  def load_state(self):

    staking_configs = STAKING_CONFIGS[self.staking_client.network]
    all_staking_contracts = list(map(lambda config: config.app_id, staking_configs))

    # get opted in staking contracts
    self.opted_in_staking_contracts = []
    self.user_staking_states = {}

    # get local states
    local_states = get_local_states(self.staking_client.algofi_client.indexer, self.address)

    for app_id, local_state in local_states.items():
      if int(app_id) in all_staking_contracts:
        staking = Staking(app_id)
        staking.load_state()
        self.user_staking_states[app_id] = UserStakingState(local_state, staking)
        self.opted_in_staking_contracts.append(app_id)