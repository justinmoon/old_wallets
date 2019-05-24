import os
import sys
import time
import bit
from random import randint

secret = 'cee1f7bd2e394189c08084be25e64411e90ed68574a329e2c768b133fdb7eba4'
key = bit.PrivateKeyTestnet.from_hex(secret)
# print('balance', key.get_balance())

def fund_addresses(addresses):
    initial_txns = set(key.get_transactions())
    for address in addresses:
        # create and broadcast tx
        fund(address)
        print('broadcasted')
    time.sleep(10)
    final_txns = set(key.get_transactions())
    txns = final_txns - initial_txns
    print(txns)
    return txns

def fund(address):
    amount = randint(1, 30_000)
    tx = key.create_transaction([
        (address, amount, 'satoshi'),
    ], 3)  # 3 b/c fee estimation on testnet is whack
    bit.network.NetworkAPI.broadcast_tx_testnet(tx)
    print(f'funded key with {amount} satoshis')
