# Security policy and limitations

## Intended use

`banking_system` is an educational, local banking simulation. It is not production banking software and must not be used to hold real funds, process real payments, or store sensitive production customer information.

## Safeguards implemented

- Passwords are stored as PBKDF2-HMAC-SHA256 hashes with unique random salts; plaintext passwords are not stored.
- Password verification validates stored hash parameters before performing the expensive key-derivation operation.
- Authentication errors use a generic invalid-credentials message to reduce account-enumeration signals.
- Repeated failed logins trigger temporary in-memory throttling (five failures and a one-minute lockout by default).
- Authenticated service operations check the customer identity associated with the session before accessing an account.
- SQL statements use parameters, and SQLite foreign keys and constraints protect relational integrity.
- Multi-record banking operations use database transactions so failures can be rolled back.
- Monetary values use `Decimal` in the application and integer kobo in SQLite.

## Known limitations

- Login throttling is in-memory, per process, and resets after restart. It is not suitable for a multi-worker or distributed deployment.
- Sessions are in-memory and are invalidated when the application process exits.
- There is no multi-factor authentication, production identity verification, role-management system, secrets manager, encrypted backup workflow, or security monitoring platform.
- The project has not undergone a professional security audit or penetration test.
- The application does not connect to a real bank or payment processor.

## Safe handling

- Use fictional customer information and test passwords only.
- Do not commit the SQLite database, credentials, secrets, or personal information.
- Keep local database files private and back them up only when working with non-sensitive demonstration data.
- Do not expose the application or database to the public internet as a banking service.

## Reporting a concern

For this learning project, document reproducible issues in the project's issue tracker or development notes. Do not include real passwords, personal data, or database files in a report.
