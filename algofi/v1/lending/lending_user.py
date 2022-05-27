# IMPORTS

# INTERFACE

class LendingUser:
    def __init__(self, lending_client, address):
        self.lending_client = lending_client
        self.address = address