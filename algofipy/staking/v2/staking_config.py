from algofipy.globals import Network


class StakingType:
    V1 = 0
    V2 = 1
    BASSET = 2
    LP = 2


class StakingConfig:
    def __init__(self, name, app_id, asset_id, type):
        self.name = name
        self.app_id = app_id
        self.asset_id = asset_id
        self.type = type


STAKING_CONFIGS = {
    Network.MAINNET: [
        StakingConfig("USDC Lend and Earn", 821882730, 818182311, StakingType.BASSET),
        StakingConfig("USDT Lend and Earn", 821882927, 818190568, StakingType.BASSET),
        StakingConfig(
            "ALGO / STBL2 Lending Pool LP", 919964388, 855717054, StakingType.LP
        ),
        StakingConfig(
            "goBTC / STBL2 Lending Pool LP", 919965019, 870151164, StakingType.LP
        ),
        StakingConfig(
            "goETH / STBL2 Lending Pool LP", 919965630, 870150187, StakingType.LP
        ),
        StakingConfig(
            "ALGO / USDC Lending Pool LP", 919964086, 919950894, StakingType.LP
        ),
        StakingConfig(
            "ALGO / BANK Lending Pool LP", 962407544, 962367827, StakingType.LP
        ),
        StakingConfig(
            "BANK / STBL2 Lending Pool LP", 900932886, 900924035, StakingType.LP
        ),
    ],
    Network.TESTNET: [
        StakingConfig("USDC Lend and Earn", 104267989, 104207173, StakingType.BASSET),
    ],
}

rewards_manager_app_id = {Network.MAINNET: 0, Network.TESTNET: 107210021}


class STAKING_STRINGS:
    admin = "a"
    rewards_program_count = "rpc"
    rps_pusher = "rpsp"
    contract_update_delay = "cud"
    contract_update_time = "cut"
    voting_escrow_app_id = "veai"
    rewards_manager_app_id = "rmai"
    external_boost_multiplier = "ebm"
    asset_id = "ai"
    user_total_staked = "uts"
    user_scaled_total_staked = "usts"
    boost_multiplier = "lm"
    user_rewards_program_counter_prefix = "urpc_"
    user_rewards_coefficient_prefix = "urc_"
    user_unclaimed_rewards_prefix = "uur_"
    total_staked = "ts"
    scaled_total_staked = "sts"
    latest_time = "lt"
    rewards_escrow_account = "rea"
    rewards_program_counter_prefix = "rpc_"
    rewards_asset_id_prefix = "rai_"
    rewards_per_second_prefix = "rps_"
    rewards_coefficient_prefix = "rc_"
    rewards_issued_prefix = "ri_"
    rewards_payed_prefix = "rp_"
    schedule_contract_update = "scu"
    increase_contract_update_delay = "icud"
    set_rewards_manager_app_id = "srma"
    set_boost_app_id = "sbai"
    set_rewards_program = "srp"
    update_rewards_program = "urp"
    opt_into_asset = "oia"
    opt_into_rewards_manager = "oirm"
    update_rewards_per_second = "urps"
    farm_ops = "fo"
    stake = "s"
    unstake = "u"
    claim_rewards = "cr"
    update_target_user = "utu"
    update_vebank_data = "update_vebank_data"
