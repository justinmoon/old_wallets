
# Notes

## `keypool.py`

- should the keypool know about transactions? should `Keypool.next()` give the same address when called multiple times without receiving any transactions in the meantime?

## `api.py`
- should `api.py` have a `get_json` method? some repetitive code in there ...
- we need to differentiate transactions
    - our sends
    - our spends
    - our unspents
