# Phase 8 — Security hardening and expanded error handling

## Delivered

- Password verification now rejects malformed salt/hash lengths, overlong
  passwords, boolean work factors, and PBKDF2 iteration counts outside the
  supported range before performing expensive hashing.
- Login attempts are throttled per normalized email address. The default is
  five consecutive failures followed by a one-minute temporary lockout.
- A successful login clears that email address's failed-attempt counter.
- Authentication failures retain a generic invalid-credentials message to
  avoid disclosing whether an email address has an account.
- SQLite connection cleanup now runs even if connection configuration fails.
- Extremely large Decimal monetary values are converted into a domain
  validation error rather than leaking Decimal quantization exceptions.
- The application shutdown message now starts on a new line.
- Regression tests cover password bounds, login throttling/reset, and extreme
  monetary input.

## Security boundaries

- Login throttling is in-memory and per process. It resets when the application
  restarts and is intended as an educational single-process safeguard.
- This project remains a local educational banking simulation. It has not
  undergone a professional security audit and must not handle real customer
  funds, production credentials, or sensitive banking data.
- Sessions remain in-memory and expire after the configured session lifetime.
- SQLite stores password hashes and salts, never plaintext passwords.

## Verification

Run the complete test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

Launch the application:

```powershell
python main.py
```
