
# IMPORTS
from algosdk.future.transaction import PaymentTxn, ApplicationOptInTxn

# INTERFACE
from algofipy.globals import Network
from algofipy.transaction_utils import get_default_params, TransactionGroup
from algofipy.governance.v1.governance_config import ADMIN_STRINGS

class GovernanceClient:

    def __init__(self, algofi_client):
        """Constructor for the algofi governance client.

        :param algofi_client: an instance of an algofi client
        :type algofi_client: :class:`AlgofiClient`
        """

        self.algofi_client = algofi_client
        self.algod = algofi_client.algod
        self.indexer = algofi_client.indexer
        self.network = algofi_client.network
        self.governance_config = GovernanceConfig[self.network]

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
    
    def get_user(user_address):
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
            params=params,
            receiver=storage_address,
            amt=1_000_000 # TODO: figure out the exact amount
        )

        txn1 = ApplicationOptInTxn(
            sender=storage_address,
            params=params,
            index=self.admin.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.storage_account_opt_in, "utf-8")],
            accounts=[user.address],
            rekey_to=self.admin.admin_address
        )

        txn2 = ApplicationOptInTxn(
            sender=user.address,
            params=params,
            index=self.admin.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.user_opt_in, "utf-8")],
            accounts=[storage_address]
        )

        txn3 = ApplicationOptInTxn(
            sender=user.address,
            params=params,
            index=self.voting_escrow.app_id,
            foreign_apps=[self.rewards_manager.app_id],
        )

        txn4 = ApplicationOptInTxn(
            sender=user.address,
            params=params,
            index=self.rewards_manager.app_id,
            app_args=[bytes(REWARDS_MANAGER_STRINGS.user_opt_in, "utf-8")],
            foreign_apps=[self.voting_escrow.app_id]
        )

        return TransactionGroup([txn0, txn1, txn2, txn3, txn4])