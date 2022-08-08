# IMPORTS

# INTERFACE

# constants

MANAGER_MIN_BALANCE = 614000 + 101000

# enums

class MarketType:
  """Enum representing the market type.
  """
  STANDARD = 0
  STBL = 1
  VAULT = 2

# strings

class MANAGER_STRINGS:
  # USER STATE
  storage_account = "sa"
  user_account = "ua"
  opted_in_market_count = "omc"
  opted_in_markets_page_prefix = "om_"

  # APPLICATION CALLS
  calculate_user_position = "cup"
  farm_ops = "fo"
  send_governance_txn = "sgt"
  send_keyreg_txn = "skt"
  send_keyreg_offline_txn = "skot"
  set_market_oracle_parameters = "smop"
  storage_account_opt_in = "saoi"
  user_asset_opt_in = "uaoi"
  user_market_close_out = "umco"
  user_market_opt_in = "umoi"
  user_opt_in = "uoi"
  validate_storage_account_txn = "vsat"
  validate_market = "vm"

class MARKET_STRINGS:
  admin = "a"
  collateral_factor = "cf"
  borrow_factor = "bf"
  b_asset_to_underlying_exchange_rate = "baer"
  underlying_cash = "uc"
  underlying_borrowed = "ub"
  underlying_reserves = "ur"
  borrow_share_circulation = "bsc"
  user_active_b_asset_collateral = "ubac"
  user_borrow_shares = "ubs"
  underlying_to_borrow_share_exchange_rate = "ubser"
  activate_market = "am"
  schedule_contract_update = "scu"
  increase_update_delays = "iud"
  remove_underlying_collateral = "ruc"
  remove_b_asset_collateral = "rbc"
  remove_reserves = "rr"
  borrow = "b"
  liquidate = "l"
  mint_b_asset = "mba"
  add_underlying_collateral = "auc"
  add_b_asset_collateral = "abc"
  burn_b_asset = "br"
  repay_borrow = "rb"
  seize_collateral = "sc"
  contract_opt_in = "coi"
  contract_update_delay = "cud"
  contract_update_time = "cut"
  oracle_app_id = "oai"
  oracle_price_field_name = "opfn"
  oracle_price_scale_factor = "opsf"
  base_interest_rate = "bir"
  base_interest_slope = "bis"
  quadratic_interest_amplification_factor = "eiaf"
  target_utilization_ratio = "tur"
  b_asset_circulation = "bac"
  latest_time = "lt"
  borrow_index = "bi"
  implied_borrow_index = "ibi"
  reserve_factor = "rf"
  new_reserve_factor = "nrf"
  new_collateral_factor = "ncf"
  new_borrow_factor = "nbf"
  new_base_interest_rate = "nbir"
  new_base_interest_slope = "nbis"
  new_quadratic_interest_amplification_factor = "neiaf"
  new_target_utilization_ratio = "ntur"
  new_oracle_app_id = "no"
  new_oracle_price_scale_factor = "nopsf"
  new_oracle_price_field_name = "nopfn"
  param_update_delay = "pud"
  param_update_time = "put"
  oracle_update_delay = "oud"
  oracle_update_time = "out"
  schedule_param_update = "spu"
  execute_param_update = "epu"
  schedule_oracle_update = "sou"
  execute_oracle_update = "eou"

  user_rewards_program_number_prefix = "urpn_"
  user_latest_rewards_index_prefix = "ulri_"
  user_unclaimed_rewards_prefix = "uur_"

  rewards_latest_time = "rlt"
  rewards_admin_prefix = "ra_"
  rewards_program_state_prefix = "rps_"
  rewards_index_prefix = "ri_"

  set_rewards_admin = "sra"
  update_rewards_per_second = "urps"
  active_b_asset_collateral = "ac"
  liquidation_incentive = "li"
  liquidation_fee = "lf"
  new_liquidation_incentive = "nli"
  new_liquidation_fee = "nlf"
  manager_app_id = "mai"
  underlying_asset_id = "uai"
  b_asset_id = "bai"

  flash_loan_fee = "flf"
  flash_loan_protocol_fee = "flpf"
  max_flash_loan_ratio = "mflr"
  flash_loan = "fl"
  set_flash_loan_params = "sflp"

  farm_ops = "fo"

  interest_rate_model_update_time = "irmut"
  interest_rate_model_update_delay = "irmud"
  schedule_interest_rate_model_update = "sirmu"
  execute_interest_rate_model_update = "eirmu"

  underlying_supply_cap = "usc"
  underlying_borrow_cap = "ubc"
  set_control_state = "scs"

  # STBL MARKET VARIANT
  underlying_protocol_reserve = "upr"
  base_interest_rate_pusher = "birp"
  set_base_interest_rate_pusher = "sbirp"
  set_base_interest_rate = "sbir"
  add_to_protocol_reserve = "atpr"

  # VAULT MARKET VARIANT
  opt_in_enabled = "oie"
  set_opt_in_enabled = "soie"
  sync_vault = "sv"

  market_type = "mt"

  rewards_escrow_account = "rea"
  set_rewards_escrow_account = "srea"
  set_rewards_program = "srp"
  opt_market_into_rewards_manager = "omirm"
  reclaim_rewards_assets = "rra"
  claim_rewards = "cr"