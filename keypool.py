from io import BytesIO
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
        if not self.keys:
            self.fill()

    def fill(self):
        for _ in range(self.n):
            secret = randint(0, N)
            self.keys.append(PrivateKey(secret))
        self.save(wallet_name)  # FIXME

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
        # ugly check that we're not deleting private keys
        keypool = self.load(filename)
        secrets = [k.secret for k in keypool.keys]
        for key in self.keys:
            assert key.secret in secrets
        with open(filename, 'w') as f:
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
        for key in self.keys:
            address = key.public_key.address(testnet=self.testnet)
            for u in get_unspent(address):
                unspent.append([key, u])
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


def construct_tx_out(address, amount):
    h160 = decode_base58(address)
    script = p2pkh_script(h160)
    return TxOut(amount=amount, script_pubkey=script)


def spend(keypool, send_amount, fee=500):
    # collect inputs
    unspent = keypool.unspent()
    tx_ins = []
    input_sum = 0
    for private_key, utxo in unspent:
        if input_sum >= send_amount + fee:
            break
        input_sum += utxo.amount
        tx_in = TxIn(utxo.tx_id, utxo.index)
        tx_ins.append(tx_in)

    # make sure we have enough
    assert input_sum > send_amount + fee

    # outputs
    send_output = construct_tx_out(keypool.next_address(), send_amount)
    change_amount = input_sum - send_amount - fee
    change_output = construct_tx_out(keypool.next_address(), change_amount)

    # construct
    tx = Tx(1, tx_ins, [send_output, change_output], 0, True)

    # sign
    # FIXME
    for i in range(len(tx_ins)):
        private_key, utxo = unspent[i]
        assert tx.sign_input(i, private_key, utxo.script_pubkey)
        print(f'signed {i}')
    print(tx)

    # broadcast
    import bit
    tx_hex = tx.serialize().hex()
    print(tx_hex)
    # raises a ConnectionError if it fails
    print(bit.network.NetworkAPI.broadcast_tx_testnet(tx_hex))


    



def status(keypool):
    print('balances')
    print(keypool.balance())
    print('transactions')
    print(keypool.transactions())
    print('unspent')
    print(keypool.unspent())


if __name__ == '__main__':
    import sys
    command = sys.argv[1] 
    keypool = Keypool.load(wallet_name)

    if command == 'status':
        status(keypool)

    elif command == 'fund':
        fund_keypool(keypool)

    elif command == 'spend':
        amount = randint(5_000, 20_000)
        spend(keypool, amount)

    else:
        print('invalid command')


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

