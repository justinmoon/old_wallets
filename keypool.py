from random import randint
from unittest import TestCase

from ecc import PrivateKey, N


class Keypool:

    def __init__(self, n):
        self.n = n
        self.used = []
        self.unused = []
        self.fill()

    def fill(self):
        for _ in range(5 * self.n):
            secret = randint(0, N)
            self.unused.append(PrivateKey(secret))

    def next_private_key(self):
        private_key = self.unused.pop()
        if len(self.unused) < self.n:
            self.fill()
        self.used.append(private_key)
        return private_key

    def next_address(self):
        private_key = self.next_private_key()
        return private_key.public_key.address()

    def backup(self):
        '''save private keys to disk'''
        pass

    def from_disk(self):
        '''retrieve private keys from disk'''
        pass

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

