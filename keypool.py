from pickle import dumps, loads
from random import randint
from unittest import TestCase
from os.path import isfile

from ecc import PrivateKey, N

from api import get_balance, get_transactions, get_unspent


class Keypool:

    def __init__(self, n, testnet=True):
        self.n = n
        self.testnet = testnet
        self.used = []
        self.unused = []
        self.fill()

    def fill(self):
        for _ in range(self.n):
            secret = randint(0, N)
            self.unused.append(PrivateKey(secret))

    def next_private_key(self):
        private_key = self.unused.pop()
        if len(self.unused) == 0:
            self.fill()
        self.used.append(private_key)
        return private_key

    def next_address(self):
        private_key = self.next_private_key()
        return private_key.public_key.address(testnet=self.testnet)

    def save(self, filename):
        '''save private keys to disk'''
        with open(filename, 'wb') as f:
            data = dumps(self)
            f.write(data)

    @classmethod
    def load(cls, filename):
        '''retrieve private keys from disk'''
        with open(filename, 'rb') as f:
            data = f.read()
            return loads(data)

    def used_addresses(self):
        return [private_key.public_key.address(testnet=self.testnet)
                for private_key in self.used]

    def addresses(self):
        return [private_key.public_key.address(testnet=self.testnet)
                for private_key in self.unused]

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


wallet_name = 'wallet.dat'


def create_keypool():
    keypool = Keypool(5)
    keypool.save(wallet_name)
    print('saved')
    return keypool

def fund_keypool(keypool):
    if not keypool.used:
        keypool.next_address()
    addresses = keypool.addresses()[1:2]

    import gimme
    gimme.fund_addresses(addresses)


if __name__ == '__main__':
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

class KeypoolTests(TestCase):

    def test_fill(self):
        n = 5
        keypool = Keypool(n)
        self.assertEqual(5*n, len(keypool.unused))
        self.assertEqual(0, len(keypool.used))

    def test_next_private_key(self):
        n = 5
        keypool = Keypool(n)
        private_key = keypool.next_private_key()
        self.assertTrue(isinstance(private_key, PrivateKey))
        self.assertIn(private_key, keypool.used)
        self.assertEqual(1, len(keypool.used))
        self.assertNotIn(private_key, keypool.unused)
        self.assertEqual(5*n - 1, len(keypool.unused))

    def test_next_address(self):
        n = 5
        keypool = Keypool(n)
        address = keypool.next_address()
        self.assertEqual('1', address[0])

