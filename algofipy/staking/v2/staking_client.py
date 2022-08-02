





class StakingClient: 
    def __init__(self, algofi_client):
        self.algofi_client = algofi_client
        self.algod = this.algofi_client.algod
        self.network = self.algofi_client.network
        self.staking_configs = staking