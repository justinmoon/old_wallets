from requests import get

from helper import serialize_varint


BASE_URL = 'https://test-insight.bitpay.com/api'
ADDRESS_URL = BASE_URL + '/addr/{}'
BALANCE_URL = ADDRESS_URL + '/balance'
UNSPENT_URL = ADDRESS_URL + '/utxo'
TXS_URL = BASE_URL + '/addrs/{}/txs'
TIMEOUT = 5





def get_balance(address):
    r = get(BALANCE_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    return r.json()

def get_transactions(address):
    r = get(ADDRESS_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    return r.json()['transactions']


def get_full_transactions(addresses):
    addresses = ''.join(addresses)
    r = get(TXS_URL.format(addresses), timeout=TIMEOUT)
    if r.status_code != 200:
        raise ConnectionError
    return r.json()


class Unspent:

    def __init__(self, tx_id, index, amount, script_pubkey):
        self.tx_id = tx_id
        self.index = index
        self.amount = amount
        self.script_pubkey = script_pubkey

    def __repr__(self):
        return f'output={self.tx_id.hex()}:{self.index} amount={self.amount}'


def parse_script_pubkey(script_pubkey):
    prev_pubkey = bytes.fromhex(script_pubkey)
    # utxo['scriptPubKey'] doesn't have a varint prefix ...
    # TODO: script.from_hex() ???
    prev_pubkey = serialize_varint(len(prev_pubkey)) + prev_pubkey
    # FIXME
    from io import BytesIO
    stream = BytesIO(prev_pubkey)
    from script import Script
    return Script.parse(stream)

def get_unspent(address):
    r = get(UNSPENT_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:  # pragma: no cover
        raise ConnectionError
    print(r.json())
    return [
        Unspent(tx_id=bytes.fromhex(tx['txid']),
                index=tx['vout'],
                amount=tx['satoshis'],
                script_pubkey=parse_script_pubkey(tx['scriptPubKey']))
        for tx in r.json()
    ]
