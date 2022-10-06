
# IMPORTS
from algosdk import logic
from algosdk.future.transaction import PaymentTxn, ApplicationNoOpTxn, AssetTransferTxn, ApplicationCloseOutTxn

# INTERFACE
from algofipy.governance.v1.governance_config import VOTING_ESCROW_STRINGS, ADMIN_STRINGS, PROPOSAL_FACTORY_STRINGS
from algofipy.governance.v1.proposal import Proposal
from algofipy.state_utils import get_global_state
from algofipy.utils import int_to_bytes
from algofipy.transaction_utils import TransactionGroup, get_default_params

class Admin:

    def __init__(self, governance_client):
        """Constructor for the Admin class.

        :param governance_client: a governance client
        :type governance_client: :class:`GovernanceClient`
        """

        self.governance_client = governance_client
        self.algod = self.governance_client.algod
        self.indexer = self.governance_client.indexer
        self.admin_app_id = self.governance_client.governance_config.admin_app_id
        self.proposal_factory_app_id = self.governance_client.governance_config.proposal_factory_app_id
        self.proposal_factory_address = logic.get_application_address(self.proposal_factory_app_id)
        self.admin_address = logic.get_application_address(self.admin_app_id)

    def load_state(self):
        """Function to refresh and load all of the global and local state we need to
        keep track of on the admin, including all of the proposals that have been
        created.
        """

        # set state for the admin
        global_state_admin = get_global_state(self.indexer, self.admin_app_id)
        self.quorum_value = global_state_admin.get(ADMIN_STRINGS.quorum_value, 0)
        self.super_majority = global_state_admin.get(ADMIN_STRINGS.super_majority, 0)
        self.proposal_duration = global_state_admin.get(ADMIN_STRINGS.proposal_duration, 0)
        self.proposal_execution_delay = global_state_admin.get(ADMIN_STRINGS.proposal_execution_delay, 0)

        # setting state for the proposal factory
        global_state_proposal_factory = get_global_state(self.indexer, self.proposal_factory_app_id)

        # put into config
        self.gov_token = global_state_proposal_factory.get(PROPOSAL_FACTORY_STRINGS.gov_token, 0)
        self.proposal_template_app_id = global_state_proposal_factory.get(PROPOSAL_FACTORY_STRINGS.proposal_template, 0)
        self.minimum_vebank_to_propose = global_state_proposal_factory.get(PROPOSAL_FACTORY_STRINGS.minimum_ve_bank_to_propose, 0)

        # get the proposals created from the factory
        proposal_factory_info = self.indexer.account_info(self.proposal_factory_address)["account"]
        self.proposals = {}
        for app_object in proposal_factory_info["created-apps"]:
            self.proposals[app_object["id"]] = Proposal(self.governance_client, app_object["id"])
            self.proposals[app_object["id"]].load_state()
    
    def get_update_user_vebank_txns(self, user_calling, user_updating):
        """ Constructs a series of transactions to update a target user's vebank.

        :param user_calling: the user who is calling the transaction
        :type user_calling: :class:`AlgofiUser`
        :param user_updating: the user who is being updated
        :type user_updating: :class:`AlgofiUser`
        :return: a series of transactions to update a target user's vebank.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        params.fee = 5000
        txn0 = ApplicationNoOpTxn(
            sender=user_calling.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.update_user_vebank, "utf-8")],
            foreign_apps=[self.governance_client.voting_escrow.app_id],
            accounts=[user_updating.address, user_updating.governance.user_admin_state.storage_address]
        )

        return TransactionGroup([txn0])
    
    def get_vote_txns(self, user, proposal, for_or_against):
        """Constructs a series of transactions to vote on a proposal.

        :param user: user who is voting
        :type user: :class:`AlgofiUser`
        :param proposal: proposal being voted on
        :type proposal: :class:`Proposal`
        :return: a series of transactions to vote on a proposal.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        # update ve bank for user
        txn0 = self.get_update_user_vebank_txns(user, user)
        
        params.fee = 2000
        txn1 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.vote, "utf-8"), int_to_bytes(for_or_against)],
            foreign_apps=[proposal.app_id],
            accounts=[user.governance.user_admin_state.storage_address, logic.get_application_address(proposal_app_id)]
        )

        return txn0 + TransactionGroup([txn1])

    def get_delegate_txns(self, user, delegatee):
        """Constructs a series of transactions to delegate a user's votes to another user.

        :param user: user who is delegating
        :type user: :class:`AlgofiUser`
        :param delegatee: user who is being delegated to
        :type delegatee: :class:`AlgofiUser`
        :return: a series of transactions to delegate a user's votes to another user.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.delegate, "utf-8")],
            foreign_apps=[proposal.app_id],
            accounts=[user.governance.user_admin_state.storage_address, delegatee.governance.user_admin_state.storage_address]
        )

        return TransactionGroup([txn0])

    def get_validate_txns(self, user, proposal):
        """Constructs a series of transactions that will validate a specific proposal.

        :param user: user who is trying to validate a proposal
        :type user: :class:`AlgofiUser`
        :param proposal: the proposal to validate
        :type proposal: :class:`Proposal`
        :return: a series of transactions that will validate a specific proposal.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.validate, "utf-8")],
            foreign_apps=[proposal.app_id],
            accounts=[logic.get_application_address(proposal.app_id)]
        )

        return TransactionGroup([txn0])

    def get_undelegate_txns(self, user):
        """Constructs a series of transactions that will undelegate a user from their
        current delegatee.

        :param user: user who is undelegating
        :type user: :class:`AlgofiUser`
        :return:  series of transactions that will undelegate a user from their
        current delegatee.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.undelegate, "utf-8")],
            accounts=[user.governance.user_admin_state.storage_address, user.governance.user_admin_state.delegating_to]
        )

        return TransactionGroup([txn0])

    def get_delegated_vote_txns(calling_user, voting_user, proposal):
        """Constructs a series of transactions that will make a user vote on a
        proposal as their delegatee has.

        :param calling_user: user who is calling the delegated vote transaction
        :type calling_user: :class:`AlgofiUser`
        :param voting_user: user who is voting
        :type voting_user: :class:`AlgofiUser`
        :param proposal: proposal being voted on
        :type proposal: :class:`AlgofiUser`
        :return: a series of transactions that will make a user vote on a proposal
        as their delegatee has.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        # update ve bank for user
        txn0 = self.get_update_user_vebank_txns(user, user)

        txn1 = ApplicationNoOpTxn(
            sender=calling_user.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.delegated_vote, "utf-8")],
            foreign_apps=[proposal.app_id, self.governance_client.voting_escrow.app_id],
            accounts=[
                voting_user.address,
                voting_user.governance.user_admin_state.storage_address,
                voting_user.governance.user_admin_state.delegating_to,
                logic.get_application_address(proposal.app_id)
            ]
        )

        return txn0 + TransactionGroup([txn1])

    def close_out_from_proposal_txns(self, user_calling, user_closing_out, proposal):
        """Constructs a series of transactions which will close out a target user from a proposal.

        :param user_calling: user who is calling the transaction
        :type user_calling: :class:`AlgofiUser`
        :param user_closing_out: user who is closing out
        :type user_closing_out: :class:`AlgofiUser`
        :param proposal: proposal being closed out of 
        :type proposal: :class:`Proposal`
        :return: a series of transactions which will close out a target user from a proposal.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        params.fee = 3000
        txn0 = ApplicationCloseOutTxn(
            sender=user_calling.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.close_out_from_proposal, "utf-8")],
            accounts=[logic.get_application_address(proposal.app_id), user_close_out.governance.user_admin_state.storage_address],
            foreign_apps=[proposal.app_id]
        )

        return TransactionGroup([txn0])

    def get_set_open_to_delegation_txns(self, user):
        """Constructs a series of transactions to set a user open to delegation.

        :param user: user who is setting themselves open to delegation
        :type user: :class:`AlgofiUser`
        :return: a series of transactions to set a user open to delegation.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.set_open_to_delegation, "utf-8")],
            accounts=[user.governance.user_admin_state.storage_address]
        )

        return TransactionGroup([txn0])

    def get_set_not_open_to_delegation_txns(self, user):
        """Constructs a series of tranactions to set a user not open to delegation.

        :param user: user who is setting themselves not open to delegation
        :type user: :class:`AlgofiUser`
        :return: a series of tranactions to set a user not open to delegation.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.admin_app_id,
            app_args=[bytes(ADMIN_STRINGS.set_not_open_to_delegation, "utf-8")],
            accounts=[user.governance.user_admin_state.storage_address]   
        )

        return TransactionGroup([txn0])
    
    def get_create_proposal_txns(self, user, title, link):
        """Constructs a series of transactions to create a proposal.

        :param user: user who is trying to create the transaction
        :type user: :class:`AlgofiUser`
        :param title: title of the proposal to be created
        :type title: str
        :param link: link of the proposal to be created
        :type link: str
        :return: a series of transactions to create a proposal.
        :rtype: :class:`TransactionGroup`
        """

        params = get_default_params(self.algod)

        txn0 = PaymentTxn(
            sender=user.address,
            sp=params,
            receiver=self.proposal_factory_address,
            amt=4_000_000 # TODO: figure out the exact amount
        )

        txn1 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.proposal_factory_app_id,
            app_args=[bytes(PROPOSAL_FACTORY_STRINGS.validate_user_account, "utf-8")]
        )

        # TODO: find out if fee is correct
        params.fee = 6000
        txn2 = ApplicationNoOpTxn(
            sender=user.address,
            sp=params,
            index=self.proposal_factory_app_id,
            app_args=[
                bytes(PROPOSAL_FACTORY_STRINGS.create_proposal, "utf-8"),
                bytes(title, "utf-8"),
                bytes(link, "utf-8")
            ],
            accounts=[user.address],
            foreign_apps=[self.governance_client.voting_escrow.app_id, self.proposal_template_app_id, self.admin_app_id]
        )

        return TransactionGroup([txn0, txn1, txn2])