# Phase 7 — Interactive command-line interface

## Delivered

- Interactive welcome menu with customer registration, login, and exit.
- Customer dashboard with account listing, savings/current account creation,
  account management, password changes, and logout.
- Account menu with balance display, deposits, withdrawals, transfers,
  transaction history, and text statements.
- Password prompts use `getpass` so passwords are not echoed in the terminal.
- Money input is parsed directly into `Decimal`; no binary floating-point
  conversion is used for financial operations.
- NGN formatting and readable transaction/account summaries.
- CLI uses the existing `AuthService` wrappers for authenticated operations.
  Account creation obtains the customer ID from the active session.
- Input/output/password functions are injectable for automated CLI tests.
- `main.py` initializes the SQLite-backed services using `banking_system.db`.

## Run the application

From the project root:

```powershell
python main.py
```

The SQLite database is created in the project root on first run. Customer,
account, and transaction records persist between application runs. In-memory
login sessions are cleared when the application exits, as documented in
Phase 6.

## Run all tests

```powershell
python -m unittest discover -s tests -v
```

## Security and scope

The CLI never asks for a customer ID to perform customer operations. The
authenticated session determines the customer identity, and `AuthService`
enforces account ownership for account access and financial operations.
Passwords are entered using a hidden terminal prompt and are never printed by
the CLI. This remains an educational simulation, not production banking
software.
