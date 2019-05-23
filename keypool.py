from io import BytesIO
from pickle import dumps, loads
from random import randint
from unittest import TestCase
from os.path import isfile

from ecc import PrivateKey, N
from tx import TxOut, TxIn, Tx

from api import get_balance, get_transactions, get_unspent

from helper import (
    decode_base58,
    SIGHASH_ALL,
    serialize_varint
)

from script import p2pkh_script, Script


from pprint import pprint


class Keypool:

    def __init__(self, n, keys=None, testnet=True):
        self.n = n
        self.testnet = testnet
        if not keys:
            keys = []
        self.keys = keys
        self.fill()

    def fill(self):
        for _ in range(self.n):
            secret = randint(0, N)
            self.keys.append(PrivateKey(secret))

    def next_key(self):
        # return the first key that hasn't seen any transactions
        for key in self.keys:
            address = key.public_key.address(testnet=self.testnet)
            if len(get_transactions(address)) == 0:
                return key
        # if all keys have seen transactions, generate more keys
        # and return the first one
        index = len(self.keys)
        self.fill()
        return self.keys[index]

    def next_address(self):
        return self.next_key().public_key.address(testnet=self.testnet)

    def save(self, filename):
        '''save private keys to disk'''
        with open(filename, 'wb') as f:
            f.writelines([
                key.hex() + '\n' for key in self.keys
            ])

    @classmethod
    def load(cls, filename):
        '''retrieve private keys from disk'''
        with open(filename, 'r') as f:
            data = f.read()
            hex_keys = data.strip().split('\n')
            keys = [PrivateKey(int(hex_key, 16)) for hex_key in hex_keys]
            return cls(len(keys), keys)

    def addresses(self):
        return [private_key.public_key.address(testnet=self.testnet)
                for private_key in self.keys]

    def balance(self):
        '''retrieve total balance'''
        balance = 0
        for address in self.addresses():
            balance += get_balance(address)
        return balance

    def transactions(self):
        '''retrieves all transactions'''
        transactions = []
        for address in self.addresses():
            transactions.extend(get_transactions(address))
        return transactions

    def unspent(self):
        unspent = []
        for address in self.addresses():
            unspent.extend(get_unspent(address))
        return unspent


wallet_name = 'secrets'


def create_keypool():
    keypool = Keypool(5)
    keypool.save(wallet_name)
    print('saved')
    return keypool

def fund_keypool(keypool):
    addresses = keypool.addresses()
    import gimme
    gimme.fund_addresses(addresses)


def spend(keypool, send_amount, fee=500):
    # collect inputs
    unspent = keypool.unspent()
    tx_ins = []
    input_sum = 0
    prev_addresses = []  # FIXME
    prev_script_pubkeys = []  # FIXME
    while input_sum < send_amount + fee:
        utxo = unspent.pop(0)
        prev_address = utxo['address']
        prev_addresses.append(prev_address)

        prev_amount = utxo['satoshis']
        input_sum += prev_amount

        prev_tx = bytes.fromhex(utxo['txid'])
        prev_index = utxo['vout']
        # utxo['scriptPubKey'] doesn't have a varint prefix ...
        prev_pubkey = bytes.fromhex(utxo['scriptPubKey'])
        prev_pubkey = serialize_varint(len(prev_pubkey)) + prev_pubkey
        stream = BytesIO(prev_pubkey)
        prev_script_pubkey = Script.parse(stream)
        prev_script_pubkeys.append(prev_script_pubkey)
        tx_in = TxIn(prev_tx, prev_index)
        tx_ins.append(tx_in)

    assert input_sum > send_amount + fee

    # send
    # TODO: make an address_to_output function
    send_address = keypool.next_address()
    send_h160 = decode_base58(send_address)
    send_script = p2pkh_script(send_h160)
    send_output = TxOut(amount=send_amount,
                        script_pubkey=send_script)

    # change
    fee = 500
    change_address = keypool.next_address()
    change_amount = input_sum - send_amount - fee
    change_h160 = decode_base58(prev_address)
    change_script = p2pkh_script(change_h160)
    change_output = TxOut(amount=change_amount, 
                          script_pubkey=change_script)

    # construct
    tx = Tx(1, tx_ins, [send_output, change_output], 0, True)

    # sign
    # FIXME
    private_key = None
    for i in range(len(tx_ins)):
        print(f'signing {i}')
        prev_address = prev_addresses[i]
        prev_script_pubkey = prev_script_pubkeys[i]
        for key in keypool.keys:
            if key.public_key.address(testnet=keypool.testnet) == prev_address:
                private_key = key
                break
        if private_key is None:
            raise Exception('private key not found')
        assert tx.sign_input(i, private_key, prev_script_pubkey)
        print('signed')
    print(tx)

    # broadcast
    import bit
    tx_hex = tx.serialize().hex()
    print(tx_hex)
    # raises a ConnectionError if it fails
    print(bit.network.NetworkAPI.broadcast_tx_testnet(tx_hex))


    



def main():
    if isfile(wallet_name):
        keypool = Keypool.load(wallet_name)
    else:
        keypool = create_keypool()

    # fund_keypool(keypool)
    print('balances')
    print(keypool.balance())
    print('transactions')
    print(keypool.transactions())
    print('unspent')
    print(keypool.unspent())

if __name__ == '__main__':
    # main()
    keypool = Keypool.load(wallet_name)
    amount = randint(5_000, 20_000)
    spend(keypool, amount)

    

class KeypoolTests(TestCase):

    def test_fill(self):
        n = 5
        keypool = Keypool(n)
        self.assertEqual(5*n, len(keypool.keys))
        self.assertEqual(0, len(keypool.used))

    def test_next_private_key(self):
        n = 5
        keypool = Keypool(n)
        private_key = keypool.next_private_key()
        self.assertTrue(isinstance(private_key, PrivateKey))
        self.assertIn(private_key, keypool.used)
        self.assertEqual(1, len(keypool.used))
        self.assertNotIn(private_key, keypool.keys)
        self.assertEqual(5*n - 1, len(keypool.keys))

    def test_next_address(self):
        n = 5
        keypool = Keypool(n)
        address = keypool.next_address()
        self.assertEqual('1', address[0])

