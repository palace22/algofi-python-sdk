# IMPORTS

# external
from algosdk.future.transactions import *
from algosdk.logic import get_application_address

# global
from ..globals import ALGO_ASSET_ID
from ..utils import *
from ..transaction_utils import *

# local
from lending_config import MANAGER_MIN_BALANCE, MANAGER_STRINGS
from manager_config import ManagerConfig

# INTERFACE

class Manager:
    def __init__(self, lending_client, manager_config):
        self.lending_client = lending_client
        self.algod = self.lending_client.algod
        self.indexer = self.lending_client.indexer
        self.app_id = manager_config.app_id
        self.address = get_application_address(self.app_id)

    # TRANSACTION BUILDERS

    def getOptInTxns(self, user, storage_address):
        params = get_default_params(self.algod)
        
        # fund storage account
        txn0 = get_payment_txn(user.address, params, storage_address, MANAGER_MIN_BALANCE, ALGO_ASSET_ID)
        
        # storage account opt in and rekey
        app_args1 = [bytes(MANAGER_STRINGS.storage_account_opt_in)]
        txn1 = ApplicationOptInTxn(storage_address, params, self.app_id, app_args1, rekey_to=get_application_address(self.app_id))
        
        # user opt in
        app_args2 = [bytes(MANAGER_STRINGS.user_opt_in)]
        accounts2 = [storage_address]
        txn2 = ApplicationOptInTxn(user.address, params, self.app_id, app_args2, account=accounts2)
        
        return TransactionGroup([txn0, txn1, txn2])
    
    def getOptOutTxns(self, user):
        params = get_default_params(self.algod)
        
        # close out of manager
        params.fee = 2000
        accounts0 = user.lending.storage_address
        txn0 = ApplicationCloseOutTxn(user.address, params, self.app_id, [], accounts=accounts0)
        
        return TransactionGroup([txn0])
    
    def getMarketOptInTxns(self, user, market):
        params = get_default_params(self.algod)
        
        # fund storage account
        txn0 = get_payment_txn(user.address, params, user.lending.storage_address, market.local_min_balance, ALGO_ASSET_ID)
        
        # validate market
        app_args1 = [bytes(MANAGER_STRINGS.validate_market)]
        accounts1 = [market.address]
        foreign_apps1 = [market.app_id]
        txn1 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args1, accounts=accounts1, foreign_apps=foreign_apps1)
        
        # opt into market
        params.fee = 2000
        app_args2 = [bytes(MANAGER_STRINGS.user_market_opt_in)]
        accounts2 = [user.lending.storage_address]
        foreign_apps2 = [market.app_id]
        txn2 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args2, accounts=accounts2, foreign_apps=foreign_apps2)
        
        return TransactionGroup([txn0, txn1, txn2])
    
    def getMarketOptOutTxns(self, user, market):
        params = get_default_params(self.algod)
        
        page, offset = user.get_market_offset(market.app_id)
        
        # opt out of market
        params.fee = 3000
        app_args0 = [bytes(MANAGER_STRINGS.user_market_close_out), int_to_bytes(page) + int_to_bytes(offset)]
        accounts0 = [user.lending.storage_address]
        foreign_apps0 = [market.app_id]
        txn0 = ApplicationNoOpTxn(user.address, params, self.app_id, app_args0, accounts=accounts0, foreign_apps=foreign_apps0)
        
        return TransactionGroup([txn0])