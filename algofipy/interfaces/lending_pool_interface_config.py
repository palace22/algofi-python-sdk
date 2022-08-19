# IMPORTS

# external

# local

# global
from algofipy.globals import Network
from algofipy.amm.v1.amm_config import PoolType

# INTERFACE

# constants

class LendingPoolInterfaceConfig:

    def __init__(self, app_id, asset1_id, asset2_id, lp_asset_id, market1_app_id, market2_app_id,
                lp_market_app_id, pool_app_id, pool_type, op_farm_app_id):
        self.app_id = app_id
        self.asset1_id = asset1_id
        self.asset2_id = asset2_id
        self.lp_asset_id = lp_asset_id
        self.market1_app_id = market1_app_id
        self.market2_app_id = market2_app_id
        self.lp_market_app_id = lp_market_app_id
        self.pool_app_id = pool_app_id
        self.pool_type = pool_type
        self.op_farm_app_id = op_farm_app_id

LENDING_POOL_INTERFACE_CONFIGS = {
    Network.MAINNET: [
        LendingPoolInterfaceConfig(41198034, 31566704, 841126810, 841171328, 818182048, 841145020, 841194726, 841170409, PoolType.NANOSWAP, 841189050), # bUSDC / bSTBL2
    ],
    Network.TESTNET: [
        LendingPoolInterfaceConfig(104532133, 104194013, 104210500, 104228491, 104207076, 104213311, 104238373, 104228342, PoolType.NANOSWAP, 104240608), # bUSDC / bSTBL2
    ]
}

# STRING CONTSTANTS

class LENDING_POOL_INTERFACE_STRINGS:

  market1_app_id = "market1_app_id"
  market2_app_id = "market2_app_id"
  lp_market_app_id = "lp_market_app_id"
  lending_manager_app_id = "lending_manager_app_id"
  pool_app_id = "pool_app_id"
  pool_manager_app_id = "pool_manager_app_id"
  op_farm_app_id = "op_farm_app_id"
  asset1_id = "asset1_id"
  asset2_id = "asset2_id"
  b_asset1_id = "b_asset1_id"
  b_asset2_id = "b_asset2_id"
  lp_asset_id = "lp_asset_id"
  
  pool_step_1 = "pool_step_1"
  pool_step_2 = "pool_step_2"
  pool_step_3 = "pool_step_3"
  pool_step_4 = "pool_step_4"
  pool_step_5 = "pool_step_5"
  pool_step_6 = "pool_step_6"
  pool_step_7 = "pool_step_7"

  burn_step_1 = "burn_step_1"
  burn_step_2 = "burn_step_2"
  burn_step_3 = "burn_step_3"
  burn_step_4 = "burn_step_4"

  swap_step_1 = "swap_step_1"
  swap_step_2 = "swap_step_2"
  swap_step_3 = "swap_step_3"
  swap_step_4 = "swap_step_4"
  swap_step_5 = "swap_step_5"
    
  swap_for_exact = "swap_for_exact"
  swap_exact_for = "swap_exact_for"