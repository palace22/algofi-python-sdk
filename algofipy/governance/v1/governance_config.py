# IMPORTS

# INTERFACE
from algofipy.globals import Network


class GovernanceConfig:
    def __init__(
        self,
        admin_app_id,
        voting_escrow_app_id,
        proposal_factory_app_id,
        rewards_manager_app_id,
        governance_token,
    ):
        """Constructor for the governance config clas

        :param admin_app_id: admin app id
        :type admin_app_id: int
        :param voting_escrow_app_id: voting escrow app id
        :type voting_escrow_app_id: int
        :param proposal_factory_app_id: proposal factory app id
        :type proposal_factory_app_id: int
        :param rewards_manager_app_id: rewards manager app id
        :type rewards_manager_app_id: int
        :param governance_token: governance token asset id
        :type governance_token: int
        """

        self.admin_app_id = admin_app_id
        self.voting_escrow_app_id = voting_escrow_app_id
        self.proposal_factory_app_id = proposal_factory_app_id
        self.rewards_manager_app_id = rewards_manager_app_id
        self.governance_token = governance_token
        self.voting_escrow_max_time_lock_seconds = 60 * 60 * 24 * 365 * 4
        self.voting_escrow_min_time_lock_seconds = 60 * 60 * 24 * 7


GOVERNANCE_CONFIGS = {
    Network.MAINNET: GovernanceConfig(
        900653388, 900653165, 900653632, 900652834, 900652777
    ),
    Network.TESTNET: GovernanceConfig(
        107210614, 107210153, 107211052, 107210021, 107212062
    ),
}


class ProposalConfig:
    def __init__(self, app_id):
        """Constructor for the proposal config class.

        :param app_id: proposal app id
        :type app_id: int
        """

        self.app_id = app_id


class VOTING_ESCROW_STRINGS:
    admin_contract_app_id = "acid"
    asset_id = "ai"
    claim = "c"
    contract_update_delay = "cud"
    contract_update_approval_hash = "cuah"
    contract_update_clear_hash = "cuch"
    contract_update_time = "cut"
    dao_address = "da"
    emergency_dao_address = "eda"
    extend_lock = "el"
    increase_contract_update_delay = "icud"
    increase_lock_amount = "ila"
    lock = "l"
    total_locked = "tl"
    total_vebank = "tv"
    update_dao_address = "uda"
    update_emergency_dao_address = "ueda"
    update_vebank_data = "uvb"
    user_amount_locked = "aal"
    user_amount_vebank = "aav"
    user_lock_duration = "uld"
    user_lock_start_time = "ulst"
    user_last_update_time = "ulut"
    user_boost_multiplier = "bm"
    rewards_manager_app_id = "rmid"
    schedule_contract_update = "scu"
    set_gov_token_id = "sgti"
    set_rewards_manager_app_id = "srmai"
    set_admin_contract_app_id = "sacai"


class ADMIN_STRINGS:
    admin = "a"
    cancel_proposal = "cp"
    canceled_by_emergency_dao = "cbed"
    contract_update_approval_hash = "cuah"
    contract_update_clear_hash = "cuch"
    contract_update_delay = "cud"
    contract_update_time = "cut"
    close_out_from_proposal = "cofp"
    delegate = "d"
    delegator_count = "dc"
    delegating_to = "dt"
    delegated_vote = "devo"
    emergency_dao_address = "eda"
    emergency_multisig = "em"
    execute = "e"
    executed = "ex"
    execution_time = "ext"
    fast_track_proposal = "ftp"
    increase_contract_update_delay = "icud"
    proposal_duration = "pd"
    num_proposals_opted_into = "npoi"
    open_to_delegation = "otd"
    proposal_app_id = "pai"
    proposal_contract_opt_in = "coi"
    proposal_execution_delay = "ped"
    proposal_factory_address = "pfa"
    quorum_value = "qv"
    schedule_contract_update = "scu"
    set_executed = "sex"
    set_proposal_duration = "spd"
    set_not_open_to_delegation = "snotd"
    set_open_to_delegation = "sotd"
    set_proposal_execution_delay = "sped"
    set_proposal_factory_address = "spfi"
    set_quorum_value = "sqv"
    set_super_majority = "ssm"
    set_voting_escrow_app_id = "sveai"
    super_majority = "sm"
    storage_account = "sa"
    storage_account_close_out = "saco"
    storage_account_opt_in = "saoi"
    undelegate = "ud"
    user_account = "ua"
    user_close_out = "uco"
    user_opt_in = "uoi"
    validate = "va"
    vote = "vo"
    vote_close_time = "vct"
    votes_against = "va"
    votes_for = "vf"
    voting_escrow_app_id = "veai"
    update_user_vebank = "uuv"
    vebank = "vb"


class PROPOSAL_FACTORY_STRINGS:
    admin = "a"
    admin_app_id = "aai"
    contract_update_approval_hash = "cuah"
    contract_update_clear_hash = "cuch"
    contract_update_delay = "cud"
    contract_update_time = "cut"
    create_proposal = "cp"
    dao_address = "da"
    emergency_dao_address = "eda"
    gov_token = "gt"
    increase_contract_update_delay = "icud"
    proposal_template = "pt"
    minimum_ve_bank_to_propose = "mvbtp"
    update_dao_address = "uda"
    update_emergency_dao_address = "ueda"
    set_voting_escrow_app_id = "sveai"
    set_proposal_template = "spt"
    schedule_contract_update = "scu"
    set_admin_app_id = "saai"
    set_minimum_ve_bank_to_propose = "smvbtp"
    validate_user_account = "vua"
    voting_escrow_app_id = "veai"


class PROPOSAL_STRINGS:
    create_transaction = "ct"
    creator_of_proposal = "cop"
    for_or_against = "foa"
    link = "l"
    opt_into_admin = "oia"
    template_id = "ti"
    title = "t"
    user_close_out = "uco"
    user_vote = "uv"
    voting_amount = "vamt"


class REWARDS_MANAGER_STRINGS:
    admin = "a"
    asset_id = "ai"
    contract_opt_in = "coi"
    contract_update_approval_hash = "cuah"
    contract_update_clear_hash = "cuch"
    contract_update_delay = "cud"
    contract_update_time = "cut"
    epoch = "e"
    epoch_start = "es"
    epoch_end = "ee"
    epoch_amount = "ea"
    epoch_rps = "erps"
    epoch_expiration_delay = "eed"
    emitter_app_id = "eaid"
    next_epoch_votes_received = "nevr"
    num_registered_contracts = "nrc"
    staking_contract_to_opt_in = "scoi"
    user_epoch = "ue"
    user_total_votes = "utv"
    user_votes_used = "uvu"
    voting_escrow_app_id = "veid"
    votes_received = "vr"
    set_emitter_app_id = "seai"
    set_voting_escrow_app_id = "sveai"
    set_gov_token_id = "sgti"
    dao_begin_next_epoch = "dbne"
    emitter_begin_next_epoch = "ebne"
    vote = "v"
    sync_staking_contract = "ssc"
    stage_contract_opt_in = "scoi"
    dao_address = "da"
    emergency_dao_address = "eda"
    schedule_contract_update = "scu"
    increase_contract_update_delay = "icud"
    update_dao_address = "uda"
    update_emergency_dao_address = "ueda"
    user_opt_in = "uoi"
    set_epoch_expiration_delay = "seed"
    reclaim_rewards = "rr"
    sync_voter = "su"


class GLOBAL_EMITTER_STRINGS:
    contract_update_approval_hash = "cuah"
    contract_update_clear_hash = "cuch"
    contract_update_delay = "cud"
    contract_update_time = "cut"
    dao_address = "da"
    emergency_dao_address = "eda"
    fund = "f"
    funding_epoch = "fe"
    funding_epoch_duration = "fed"
    gov_asset_id = "gai"
    increase_contract_update_delay = "icud"
    halt_funding = "hf"
    is_funding_halted = "ifh"
    opt_in_gov_token = "oigt"
    rate = "r"
    rate_reduction_coefficient = "rrc"
    restart_funding = "rf"
    rewards_manager_app_id = "rmai"
    schedule_contract_update = "scu"
    start_epoch_supply = "ses"
    start_funding = "sf"
    start_funding_epoch_time = "sfet"
    terminal_supply = "ts"
    total_supply_emitted = "tse"
    update_dao_address = "uda"
    update_emergency_dao_address = "ueda"
    update_rewards_manager_app_id = "urmai"
