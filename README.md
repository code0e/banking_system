# Banking Management System (`banking_system`)

An educational Python banking-management simulation demonstrating OOP, exact monetary arithmetic, SQLite persistence, repositories, transactions, and automated testing. This is a learning project, **not production banking software**.

## Features

- Customer registration and case-insensitive unique email addresses.
- Savings and current accounts with configurable minimum-balance and overdraft rules.
- Deposits, withdrawals, transaction history, statements, and transfers.
- Ownership checks and custom banking exceptions.
- Optional SQLite-backed persistence while retaining the original in-memory service mode.
- Integer-kobo storage in SQLite; `Decimal` remains the domain representation.
- Parameterized SQL, foreign keys, database constraints, indexes, and explicit commit/rollback handling.
- Persistent paired transfer entries and balances written in one database transaction.
- Customer authentication with salted PBKDF2-HMAC-SHA256 password hashing.
- Separate credential storage; plaintext passwords are never stored.
- Expiring in-memory sessions, logout, password changes, and session revocation.
- Authenticated account-operation wrappers that enforce customer ownership.

## Project structure

```text
banking_system/
├── database/                 # SQLite schema and connection manager
├── models/                   # Customer, accounts, transactions
├── repositories/             # Customer, account, transaction, credential persistence
├── services/                 # BankService and AuthService
├── utils/                    # Validation and password security
├── tests/                    # Unit and persistence integration tests
├── exceptions.py
├── main.py
├── README.md
├── PHASE_5_NOTES.md
└── PHASE_6_NOTES.md
```

## Requirements and setup

Python 3.10+ is sufficient. The project uses only the Python standard library.

```powershell
cd C:\Users\hp\Desktop\PYTHON\banking_system
python -m unittest discover -s tests -v
```

## Use persistent storage

`BankService()` keeps the original in-memory behavior. To enable SQLite persistence, supply a `Database` instance:

```python
from decimal import Decimal
from database import Database
from services.bank_service import BankService

bank = BankService(Database("banking_system.db"))
customer = bank.register_customer("Ada Lovelace", "ada@example.com")
account = bank.create_current_account(customer.customer_id)
bank.deposit(account.account_number, Decimal("250.00"))
```

On the next application start, create a new service with the same database path; customers, accounts, balances, and transaction history are loaded automatically.

## Customer authentication

Use `AuthService` with the same SQLite database as `BankService`. Passwords must contain 10–128 characters, including uppercase, lowercase, a number, and a special character. The application stores only a PBKDF2-HMAC-SHA256 digest, a unique random salt, and the work factor.

```python
from database import Database
from services.auth_service import AuthService

database = Database("banking_system.db")
auth = AuthService(database)
customer = auth.register(
    "Ada Lovelace", "ada@example.com", "SecurePass123!"
)
session = auth.login("ada@example.com", "SecurePass123!")
accounts = auth.get_customer_accounts(session.token)
auth.logout(session.token)
```

Sessions are held in memory and expire after one hour by default. They are invalidated on application restart. Use the authenticated `AuthService` wrappers for customer-facing operations; those wrappers pass the authenticated customer ID into `BankService` ownership checks.

## Monetary storage

The domain layer uses `Decimal`. SQLite stores amounts as integer kobo (100 kobo = NGN 1.00), avoiding binary floating-point rounding. Do not pass Python `float` values to monetary methods.

## Test coverage

Run the complete suite with `python -m unittest discover -s tests -v`. Tests cover existing model/service/transfer behavior, database constraints and rollback, repository CRUD and reconstruction, restart persistence, overdraft restoration, transaction history, persisted transfers, password hashing, login, sessions, password changes, and authenticated ownership checks.

## Development phases

1. Core models — complete.
2. Customer and account management — complete.
3. Deposits, withdrawals, and transaction history — complete.
4. Money transfers — complete.
5. SQLite persistence — implementation and automated tests included here.
6. Customer authentication and password hashing — implemented and tested.
7. Interactive command-line interface.
8. Expanded security and error-handling review.
9. Final documentation and release.

## Educational-use disclaimer

This simulation has not been designed, audited, or approved to handle real customer funds or sensitive production banking data.
