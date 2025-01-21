from bitcoinutils.transactions import Transaction

from blockchain_query_services.services.bitcoin_rpc_services import BitcoinRPCClients


class BroadcastTransactionService:

    def __init__(self):
        self.bitcoin_rpc_client = BitcoinRPCClients.regtest()

    def __call__(self, transaction: Transaction):
        print("Current vsize: " + str(transaction.get_vsize()))
        self.bitcoin_rpc_client.send_raw_transaction(raw_tx=transaction.serialize())
        self.bitcoin_rpc_client.generate_blocks(num_blocks=1)
