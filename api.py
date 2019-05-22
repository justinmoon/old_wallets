from requests import get


BASE_URL = 'https://test-insight.bitpay.com/api'
ADDRESS_URL = BASE_URL + '/addr/{}'
BALANCE_URL = ADDRESS_URL + '/balance'
UNSPENT_URL = ADDRESS_URL + '/utxo'
TXS_URL = BASE_URL + '/addrs/{}/txs'
TIMEOUT = 5


def get_balance(address):
    r = get(BALANCE_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:
        print(r)
        raise ConnectionError
    return r.json()

def get_transactions(address):
    r = get(ADDRESS_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:
        print(r)
        raise ConnectionError
    print(r.json())
    return r.json()['transactions']


def get_full_transactions(addresses):
    addresses = ''.join(addresses)
    r = get(TXS_URL.format(addresses), timeout=TIMEOUT)
    if r.status_code != 200:
        print(r)
        raise ConnectionError
    from pprint import pprint
    pprint(r.json())
    return r.json()


def get_unspent(address):
    r = get(UNSPENT_URL.format(address), timeout=TIMEOUT)
    if r.status_code != 200:  # pragma: no cover
        raise ConnectionError
    return r.json()
    # return [
        # Unspent(currency_to_satoshi(tx['amount'], 'btc'),
                # tx['confirmations'],
                # tx['scriptPubKey'],
                # tx['txid'],
                # tx['vout'])
        # for tx in r.json()
    # ]
