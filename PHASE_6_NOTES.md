# Phase 6 — Customer authentication and password security

## Delivered

- PBKDF2-HMAC-SHA256 password hashing using Python's standard library.
- A new cryptographically random 16-byte salt for every password.
- Constant-time password digest comparison.
- Password policy: 10–128 characters, including uppercase, lowercase, a number, and a special character.
- A separate `customer_credentials` table; plaintext passwords are never persisted.
- SQLite schema version 2, which adds credentials without deleting Phase 5 customer/account/transaction data.
- Atomic customer-profile and credential registration.
- Trusted migration helper for assigning first-time credentials to existing Phase 5 customers after their identity is verified.
- Login with generic invalid-credentials errors.
- Random in-memory session tokens, one-hour default lifetime, expiry checks, and logout.
- Password change after verifying the current password; all sessions for that customer are revoked afterward.
- Authenticated wrappers for account listing, account lookup, deposits, withdrawals, transfers, history, and statements. These wrappers always pass the session customer's ID to the existing ownership checks.
- Tests for hashing, unique salts, invalid credentials, weak passwords, session lifecycle, password changes, migration, and cross-customer access.

## Main modules

- `utils/security.py`
- `repositories/user_repository.py`
- `services/auth_service.py`
- `database/schema.py`
- `database/connection.py`
- `tests/test_authentication.py`

## Usage

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


## Session and security limitations

Sessions are held in process memory and are invalidated when the application restarts. This is appropriate for the educational CLI. A production web deployment would require hardened session storage, rate limiting, audit logging, secure transport, account recovery, and a broader security review.

## Verification

Run the complete suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

The Phase 6 package was tested with the full suite: **123 tests passed**.

## Educational-use disclaimer

This project is a learning simulation and must not be used to handle real customer funds or sensitive production banking data.
