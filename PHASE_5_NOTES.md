# Phase 5 — SQLite persistence

## Delivered

- `database/schema.py`: customers, accounts, transactions, constraints, and indexes.
- `database/connection.py`: connection lifecycle, foreign-key enforcement, schema initialization, and explicit transactions.
- `repositories/customer_repository.py`: customer insert and lookup operations.
- `repositories/account_repository.py`: account persistence and correct savings/current reconstruction.
- `repositories/transaction_repository.py`: transaction history persistence and lookup.
- `BankService(Database(...))`: loads persisted records at startup and persists customer/account creation, deposits, withdrawals, and transfers.
- Integer-kobo storage with `Decimal` domain values.
- Persistent transfers update both balances and write both linked transaction entries in one SQLite transaction.
- Current-account overdraft balances and transaction history are restored after restart.

## Backward compatibility

`BankService()` without a database remains in-memory. This preserves the existing Phase 1–4 tests and gives the project an easy isolated mode for examples. Use `BankService(Database("banking_system.db"))` for the persistent application mode.

## Verification

The full test suite was run with `python -m unittest discover -s tests -v`.

Result during package preparation: **97 tests passed**.

## Important

The database file is ignored by Git. Keep backups of any local data you care about. This is an educational simulation and is not suitable for real financial services.
