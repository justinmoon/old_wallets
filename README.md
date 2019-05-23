
# Notes

## `keypool.py`

- should the keypool know about transactions? should `Keypool.next()` give the same address when called multiple times without receiving any transactions in the meantime?
- `spend()`

## `api.py`
- should `api.py` have a `get_json` method? some repetitive code in there ...
- we need to differentiate transactions
    - our sends
    - our spends
    - our unspents

    
## teaching

- every student should have a few private keys stored in local directory
- a few funded w/ p2pk, a few funded w/ p2pkh, a few unfunded
    - some can be funded when we learn to sign transactions (1 p2pk, 1 p2pkh)

    
## gameplan

- transaction signing exercise 
- fix keypool exercises
- sd wallet
- hd wallet
