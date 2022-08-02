class Staking:
    def __init__(self, app_id):
        self.app_id = app_id
    
    def load_state(self):
        print("loaded state!")