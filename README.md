# Banking Management System

**Project:** `banking_system`  
**Release:** `1.0.0`  
**Language:** Python  
**Storage:** SQLite  
**Interface:** Interactive command-line application

An educational banking-management simulation built to demonstrate object-oriented programming, service/repository architecture, exact monetary arithmetic, relational persistence, authentication, transaction handling, and automated testing.

> **Educational-use only.** This project is not production banking software. It is not designed, audited, or approved to hold real funds, process real payments, or store sensitive production customer information.

## Features

### Customers and accounts

- Customer registration with case-insensitive unique email addresses.
- Savings and current accounts.
- Unique ten-digit account numbers.
- Configurable savings minimum balance.
- Configurable current-account overdraft limit (zero by default).
- Customer account listing and account ownership checks.

### Banking operations

- Deposits and withdrawals.
- Transfers between accounts, including accounts belonging to different customers.
- Transaction history and account statements.
- Matching transfer records for both sender and recipient.
- Validation for zero, negative, non-finite, and floating-point monetary inputs.
- Transfer rollback protection so a failed transfer does not leave a partial debit or credit.

### Persistence and authentication

- SQLite persistence for customers, credentials, accounts, balances, and transactions.
- Integer-kobo monetary storage in SQLite; `Decimal` is used in the domain layer.
- Parameterized SQL, foreign keys, database constraints, and indexes.
- Explicit database transactions with commit/rollback handling.
- Password hashing using PBKDF2-HMAC-SHA256 with a unique random salt.
- In-memory expiring sessions, logout, password changes, and customer ownership enforcement.
- Temporary login throttling after repeated failed attempts.

### Command-line interface

- Customer registration and login.
- Customer dashboard and account creation.
- Account dashboard with deposit, withdrawal, transfer, transaction history, and statement options.
- Password change and logout.
- NGN currency formatting and password input that is not echoed to the terminal.

## Technology and requirements

- Python 3.10 or newer.
- SQLite (included with Python's standard library).
- No third-party Python packages are required.

Check your Python version:

```powershell
python --version
```

## Installation and launch

1. Download and extract the project folder.
2. Open PowerShell in the extracted `banking_system` directory.
3. Run the application:

```powershell
python main.py
```

The application initializes `banking_system.db` in the project root when it starts. Keep this file if you want to retain your local demonstration data. The database is excluded from source-control and release archives by `.gitignore`.

## Run the automated tests

From the project root:

```powershell
python -m unittest discover -s tests -v
```

The test suite covers account models, customer management, banking operations, transfer rules and rollback, SQLite schema and repositories, persistence across service restarts, password hashing, authentication, session expiry, ownership checks, login throttling, and CLI workflows.

## Project structure

```text
banking_system/
├── cli/
│   ├── app.py                 # Interactive terminal menus and user input
│   └── formatters.py          # NGN and account display formatting
├── database/
│   ├── connection.py          # SQLite connection and transaction handling
│   ├── schema.py              # Schema initialization and migration support
│   └── README.md              # Database implementation notes
├── models/
│   ├── account.py             # Abstract account and shared account behavior
│   ├── current_account.py     # Current-account rules
│   ├── customer.py            # Customer model
│   ├── savings_account.py     # Savings-account rules
│   └── transaction.py         # Transaction model and transaction types
├── repositories/
│   ├── account_repository.py
│   ├── customer_repository.py
│   ├── transaction_repository.py
│   └── user_repository.py     # Credential persistence
├── services/
│   ├── auth_service.py       # Registration, login, sessions, ownership wrappers
│   └── bank_service.py       # Customer, account, and banking workflows
├── tests/                    # Automated unit and integration tests
├── utils/
│   ├── security.py            # Password hashing and verification
│   └── validators.py          # Input and monetary validation
├── exceptions.py              # Domain-specific exception hierarchy
├── main.py                    # Application entry point
├── README.md
├── CHANGELOG.md
├── SECURITY.md
├── VERSION
└── PHASE_*_NOTES.md
```

## How the application is organized

The project separates responsibilities into layers:

- **Models** represent customers, accounts, and transactions and enforce account-level rules.
- **Repositories** read and write persisted records.
- **Services** coordinate customer workflows, banking operations, authentication, and ownership checks.
- **Database** manages SQLite connections, schema setup, and transaction boundaries.
- **CLI** handles terminal input/output and delegates business rules to the services.
- **Tests** verify behavior across models, services, persistence, authentication, and the interface.

This separation keeps financial rules out of the terminal interface and makes the core behavior testable without interactive input.

## Monetary precision

The domain layer uses Python's `Decimal`; SQLite stores monetary values as integer kobo, where 100 kobo equals NGN 1.00. Python `float` values are deliberately rejected by monetary operations to avoid binary floating-point representation errors.

Example for service-layer use:

```python
from decimal import Decimal

amount = Decimal("2500.50")
```

Do not construct money values from a float, for example `Decimal(2500.50)`. Use a string or an integer number of kobo where appropriate.

## Authentication notes

Passwords are validated against the project's password policy and stored as PBKDF2-HMAC-SHA256 hashes with unique random salts. Plaintext passwords are not persisted. Sessions are stored in memory, expire after their configured lifetime, and are invalidated when the application process restarts.

The login throttling mechanism is an educational, in-memory per-process safeguard. It is not a distributed rate limiter and resets when the process restarts. See [SECURITY.md](SECURITY.md) for the security boundaries and responsible-use guidance.

## Development history

The project was completed in nine development phases:

1. Core object-oriented account models.
2. Customer and account management.
3. Deposits, withdrawals, and transaction history.
4. Money transfers.
5. SQLite persistence.
6. Customer authentication and password hashing.
7. Interactive command-line interface.
8. Security hardening, expanded tests, and error handling.
9. Final documentation and release preparation.

See the `PHASE_*_NOTES.md` files for implementation notes from the later phases.

## Scope and disclaimer

This project is intended for learning, demonstration, and portfolio purposes. It does not integrate with banks or payment processors. It does not implement regulatory compliance, production-grade identity verification, multi-factor authentication, encrypted backups, operational monitoring, or professionally audited security controls. Do not use it to manage real customer funds or sensitive production data.
