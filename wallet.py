from random import randint
from os.path import isfile

from ecc import PrivateKey, N
from tx import TxIn, TxOut, Tx
from api import get_balance, get_transactions, get_unspent
from helper import decode_base58
from script import p2pkh_script


class Wallet:

    def __init__(self, private_key, filename):
        self.private_key = private_key
        self.filename = filename

    @classmethod
    def load(cls, filename):
        with open(filename, 'r') as f:
            secret_hex = f.read()
            secret = int(secret_hex, 16)
            private_key = PrivateKey(secret)
            return cls(private_key, filename)

    @classmethod
    def generate(cls, filename):
        if isfile(filename):
            raise IOError(f'"filename" already exists')
        secret = randint(0, N)
        private_key = PrivateKey(secret)
        wallet = cls(private_key, filename)
        wallet.save()
        print(f'generated private key and saved to {filename}')
        return wallet

    def save(self):
        with open(self.filename, 'w') as f:
            secret = self.private_key.hex()
            f.write(secret)
            print(f'secret saved to {self.filename}')

    def address(self):
        return self.private_key.public_key.address(testnet=True)

    def balance(self):
        return get_balance(self.address())

    def transactions(self):
        return get_transactions(self.address())

    def unspent(self):
        return get_unspent(self.address())

    def send(self, adddress, amount, fee=500):
        # collect inputs
        unspent = self.unspent()
        tx_ins = []
        input_sum = 0
        for utxo in unspent:
            if input_sum >= amount + fee:
                break
            input_sum += utxo.amount
            tx_in = TxIn(utxo.tx_id, utxo.index)
            tx_ins.append(tx_in)

        # make sure we have enough
        assert input_sum > amount + fee, 'not enough satoshis'

        # send output
        send_h160 = decode_base58(address)
        send_script = p2pkh_script(send_h160)
        send_output = TxOut(amount=amount, script_pubkey=send_script)

        # change output
        change_amount = input_sum - amount - fee
        change_h160 = decode_base58(self.address())
        change_script = p2pkh_script(change_h160)
        change_output = TxOut(amount=amount, script_pubkey=change_script)

        # construct
        tx = Tx(1, tx_ins, [send_output, change_output], 0, True)

        # sign
        for i in range(len(tx_ins)):
            utxo = unspent[i]
            assert tx.sign_input(i, self.private_key, utxo.script_pubkey)
            print(f'signed {i}')
        print(tx)

        # broadcast
        import bit
        tx_hex = tx.serialize().hex()
        print(tx_hex)
        # raises a ConnectionError if it fails
        print(bit.network.NetworkAPI.broadcast_tx_testnet(tx_hex))

if __name__ == '__main__':
    import sys

    filename = sys.argv[1]
    command = sys.argv[2]

    if command == 'generate':
        wallet = Wallet.generate(filename)

    elif command == 'fund':
        wallet = Wallet.load(filename)
        import gimme
        gimme.fund(wallet.address())
    
    elif command == 'send':
        wallet = Wallet.load(filename)
        address = sys.argv[3]
        amount = int(sys.argv[4])
        wallet.send(address, amount)

    elif command == 'status':
        wallet = Wallet.load(filename)
        print('address: ', wallet.address())
        print('balance: ', wallet.balance())
        print('transactions: ', wallet.transactions())
        print('unspent: ', wallet.unspent())

    else:
        print('generate filename | fund filename | send filename address amount | status filename')


