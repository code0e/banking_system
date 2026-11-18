# LogicBank — Banking Management System

LogicBank is an educational banking-management project built with Python.
It is designed to demonstrate object-oriented programming, monetary
validation, custom exceptions, and separation between domain models and
application services.

> **Project status:** The current implementation supports in-memory customer
> and account management, savings/current account rules, deposits,
> withdrawals, transaction history, and text statements. SQLite persistence,
> authentication, transfers, and the interactive CLI are not yet implemented.
> This is a learning project, not production banking software.

## Current features

- Register customers and prevent duplicate email addresses.
- Create savings and current accounts.
- Generate unique ten-digit account numbers.
- Keep customer and account data in memory.
- Deposit and withdraw using `Decimal` monetary values.
- Enforce savings minimum balances.
- Support optional current-account overdrafts.
- Verify account ownership when a customer ID is supplied.
- Record deposits and withdrawals in transaction history.
- Generate readable account statements in NGN.
- Use custom exceptions for expected banking and validation errors.
- Run automated tests with Python's built-in `unittest` framework.

## Technology

- Python
- Object-oriented programming (OOP)
- `Decimal` for monetary arithmetic
- Python dictionaries for the current in-memory storage layer
- `unittest` for automated tests

No third-party package is required for the current implementation.

## Project structure

```text
banking_system/
├── main.py
├── exceptions.py
├── README.md
├── models/
│   ├── __init__.py
│   ├── account.py
│   ├── customer.py
│   ├── current_account.py
│   ├── savings_account.py
│   └── transaction.py
├── services/
│   ├── __init__.py
│   └── bank_service.py
├── utils/
│   ├── __init__.py
│   └── validators.py
└── tests/
    ├── __init__.py
    ├── test_accounts.py
    ├── test_bank_service.py
    └── test_banking_operations.py
```

## Architecture

### `models/`

Contains the banking domain objects and their rules.

- `Customer` represents a bank customer.
- `BankAccount` is the abstract base class shared by account types.
- `SavingsAccount` enforces a minimum-balance rule.
- `CurrentAccount` supports an optional overdraft limit.
- `Transaction` represents a recorded account operation.

### `services/`

`BankService` coordinates customer registration, account creation, account
lookups, ownership checks, deposits, withdrawals, transaction history, and
statement generation. It delegates account-specific financial rules to the
account models.

### `utils/`

Contains reusable input-validation helpers, including monetary conversion
and non-empty string validation.

### `exceptions.py`

Defines the custom exception hierarchy used to communicate expected
validation, customer, account, and balance errors.

### `tests/`

Contains automated tests for account models, customer/account management,
and banking operations.

## Setup

1. Install Python 3.10 or newer.
2. Open PowerShell in the project directory.
3. (Optional) Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The current project uses only Python's standard library, so no package
installation is required for the existing tests.

## Run the tests

From the project root:

```powershell
python -m unittest discover -s tests -v
```

To run an individual test module:

```powershell
python -m unittest tests.test_accounts -v
python -m unittest tests.test_bank_service -v
python -m unittest tests.test_banking_operations -v
```

## Current implementation notes

- Customer and account records are stored in dictionaries owned by a
  `BankService` instance.
- Data is lost when the application process ends or a new service instance
  is created.
- The service methods accept an optional `customer_id` for ownership checks.
  A future user-facing interface should always pass the authenticated
  customer's ID for customer-initiated account operations.
- `Decimal` is used for money; do not pass Python float values to monetary
  methods.
- The current statement is a formatted text representation, not a generated
  PDF or downloadable bank document.

## Planned development phases

1. Core account and customer models.
2. Customer and account management.
3. Deposits, withdrawals, and transaction history.
4. Money transfers with atomicity and rollback.
5. SQLite persistence and database constraints.
6. Customer authentication and password hashing.
7. Interactive command-line interface.
8. Expanded tests, security review, and error-handling improvements.
9. Final documentation and release.

## Educational-use disclaimer

LogicBank is a learning simulation. It has not been designed, audited, or
approved for handling real customer funds or sensitive production banking
data. Do not use it as a real banking platform.
