# IMPORTS
from algosdk.future.transaction import PaymentTxn, ApplicationOptInTxn
from algosdk.encoding import encode_address
from base64 import b64encode, b64decode

# INTERFACE
from algofipy.globals import Network
from algofipy.transaction_utils import get_default_params, TransactionGroup
from algofipy.state_utils import format_state, get_accounts_opted_into_app
from algofipy.governance.v1.governance_config import (
    GOVERNANCE_CONFIGS,
    ADMIN_STRINGS,
    REWARDS_MANAGER_STRINGS,
    VOTING_ESCROW_STRINGS,
    PROPOSAL_STRINGS,
)
from algofipy.governance.v1.admin import Admin
from algofipy.governance.v1.voting_escrow import VotingEscrow
from algofipy.governance.v1.rewards_manager import RewardsManager
from algofipy.governance.v1.governance_user import GovernanceUser


class GovernanceClient:
    def __init__(self, algofi_client):
        """Constructor for the algofi governance client.

        :param algofi_client: an instance of an algofi client
        :type algofi_client: :class:`AlgofiClient`
        """

        self.algofi_client = algofi_client
        self.algod = algofi_client.algod
        self.indexer = algofi_client.indexer
        self.historical_indexer = algofi_client.historical_indexer
        self.network = algofi_client.network
        self.governance_config = GOVERNANCE_CONFIGS[self.network]
        self.load_state()

    def load_state(self):
        """Creates new admin, voting escrow, and rewards managers on the algofi client
        object and loads their state.
        """

        # load admin contract data
        self.admin = Admin(self)
        self.admin.load_state()

        # load voting escrow contract data
        self.voting_escrow = VotingEscrow(self)
        self.voting_escrow.load_state()

        # load rewards manager contract data
        self.rewards_manager = RewardsManager(self, self.governance_config)

    def get_user(self, user_address):
        """Gets an algofi governance user given an address.

        :param user_address: the address of the user we are interested in.
        :type user_address: str
        :return: an algofi governance user.
        :rtype: :class:`GovernanceUser`
        """

        return GovernanceUser(self, user_address)

    def get_opt_in_txns(self, user, storage_address):
        """Constructs a series of transactions to opt the user and their storage
        account into all of the necessary applications for governance including the
        admin, the voting escrow, and the rewards manager.

        :param user: user we are opting into the contracts
        :type user: :class:`AlgofiUser`
        :param storage_address: a newly created account that will serve as the
        storage account for the user on the protocol
        :type storage_address: str
        :return: a series of transactions to opt the user and their storage
        account into all of the necessary applications for governance including the
        admin, the voting escrow, and the rewards manager.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = PaymentTxn(
            sender=user.address,
            sp=params,
            receiver=storage_address,
            amt=1_000_000,  # TODO: figure out the exact amount
        )

        txn1 = ApplicationOptInTxn(
            sender=storage_address,
            sp=params,
            index=self.admin.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.storage_account_opt_in, "utf-8")],
            accounts=[user.address],
            rekey_to=self.admin.admin_address,
        )

        txn2 = ApplicationOptInTxn(
            sender=user.address,
            sp=params,
            index=self.admin.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.user_opt_in, "utf-8")],
            accounts=[storage_address],
        )

        txn3 = ApplicationOptInTxn(
            sender=user.address,
            sp=params,
            index=self.voting_escrow.app_id,
            foreign_apps=[self.rewards_manager.app_id],
        )

        txn4 = ApplicationOptInTxn(
            sender=user.address,
            sp=params,
            index=self.rewards_manager.app_id,
            app_args=[bytes(REWARDS_MANAGER_STRINGS.user_opt_in, "utf-8")],
            foreign_apps=[self.voting_escrow.app_id],
        )

        return TransactionGroup([txn0, txn1, txn2, txn3, txn4])

    def get_governor_admin_state(self):
        """Function that uses indexer to query for governors' admin state"""

        # query all users opted into admin contract
        admin_app_id = self.governance_config.admin_app_id
        admin_app_accounts = get_accounts_opted_into_app(self.indexer, admin_app_id, exclude="assets,created-apps,created-assets")

        # filter to accounts with relevant key
        user_data = {}
        storage_mapping = {}
        for user in admin_app_accounts:
            user_local_state = user.get("apps-local-state", {})
            for app_local_state in user_local_state:
                if app_local_state["id"] == admin_app_id:
                    formatted_state = format_state(app_local_state.get("key-value", []))
                    user_account = encode_address(
                        b64decode(formatted_state.get(ADMIN_STRINGS.user_account, ""))
                    )
                    if user_account:
                        open_to_delegation = formatted_state.get(
                            ADMIN_STRINGS.open_to_delegation, ""
                        )
                        delegating_to = encode_address(
                            b64decode(
                                formatted_state.get(ADMIN_STRINGS.delegating_to, "")
                            )
                        )
                        user_data[user_account] = {
                            "storage_account": user["address"],
                            "open_to_delegation": open_to_delegation,
                            "delegating_to": delegating_to,
                        }
                        storage_mapping[user["address"]] = user_account
        return (user_data, storage_mapping)

    def get_governor_voting_escrow_state(self):
        """Function that uses indexer to query for governors' voting escrow state"""

        # query all users opted into admin contract
        voting_escrow_app_id = self.governance_config.voting_escrow_app_id
        voting_escrow_app_accounts = get_accounts_opted_into_app(self.indexer, voting_escrow_app_id, exclude="assets,created-apps,created-assets")

        # filter to accounts with relevant key
        user_data = {}
        for user in voting_escrow_app_accounts:
            user_local_state = user.get("apps-local-state", {})
            for app_local_state in user_local_state:
                if app_local_state["id"] == voting_escrow_app_id:
                    formatted_state = format_state(app_local_state.get("key-value", []))
                    lock_start_time = formatted_state.get(
                        VOTING_ESCROW_STRINGS.user_lock_start_time, 0
                    )
                    amount_locked = formatted_state.get(
                        VOTING_ESCROW_STRINGS.user_amount_locked, 0
                    )
                    lock_duration = formatted_state.get(
                        VOTING_ESCROW_STRINGS.user_lock_duration, 0
                    )
                    amount_vebank = formatted_state.get(
                        VOTING_ESCROW_STRINGS.user_amount_vebank, 0
                    )
                    boost_multiplier = formatted_state.get(
                        VOTING_ESCROW_STRINGS.user_boost_multiplier, 0
                    )
                    user_data[user["address"]] = {
                        VOTING_ESCROW_STRINGS.user_lock_start_time: lock_start_time,
                        VOTING_ESCROW_STRINGS.user_amount_locked: amount_locked,
                        VOTING_ESCROW_STRINGS.user_lock_duration: lock_duration,
                        VOTING_ESCROW_STRINGS.user_amount_vebank: amount_vebank,
                        VOTING_ESCROW_STRINGS.user_boost_multiplier: boost_multiplier,
                    }
        return user_data

    def get_governor_proposal_state(self, proposal_app_id):
        """Function that uses indexer to query for governors' proposal state"""

        # query all users opted into admin contract
        proposal_app_accounts = get_accounts_opted_into_app(self.indexer, proposal_app_id, exclude="assets,created-apps,created-assets")

        # filter to accounts with relevant key
        user_data = {}
        for user in proposal_app_accounts:
            user_local_state = user.get("apps-local-state", {})
            for app_local_state in user_local_state:
                if app_local_state["id"] == proposal_app_id:
                    formatted_state = format_state(app_local_state.get("key-value", []))
                    for_or_against = formatted_state.get(
                        PROPOSAL_STRINGS.for_or_against, 0
                    )
                    voting_amount = formatted_state.get(
                        PROPOSAL_STRINGS.voting_amount, 0
                    )
                    user_data[user["address"]] = {
                        "for_or_against": for_or_against,
                        "voting_amount": voting_amount,
                    }
        return user_data
