# LogicBank Phase 4 — Money Transfers

## Included implementation

- `BankService.transfer()` coordinates transfers between any two registered
  accounts.
- The caller's optional `customer_id` is checked against the sender account.
  The recipient may belong to the same customer or another customer.
- A transfer to the same account is rejected.
- The sender's savings minimum-balance or current-account overdraft policy is
  enforced before any balance changes.
- Each transfer creates a `TRANSFER_OUT` and `TRANSFER_IN` transaction sharing
  one reference.
- If applying either transaction raises an exception, both account balances
  and transaction histories are restored to their pre-transfer snapshots.

## Apply

Extract the ZIP into the existing project root and replace the matching files.
The new `tests/test_transfers.py` should be added to the existing `tests`
directory. Do not replace the other existing test modules.

## Test

```powershell
python -m unittest discover -s tests -v
```

The previous suite had 45 tests. This phase adds 14 transfer tests, so the
expected total is 59 if all existing tests and the new tests are discovered.
The expected count is not a claim that the tests have already passed in the
user's local environment.

## Scope note

This is in-memory, single-process rollback logic for an educational project.
It is not a substitute for database transactions, concurrency controls, or
durable atomicity. Those concerns will be addressed when SQLite persistence
is implemented.
