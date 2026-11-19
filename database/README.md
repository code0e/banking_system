# SQLite persistence and schema migrations

The database stores monetary values as integer kobo, avoiding floating-point arithmetic. `Database.transaction()` uses `BEGIN IMMEDIATE` and rolls back on exceptions. Repository methods use parameterized SQL.

Schema version 2 adds `customer_credentials`, a separate table for salted password digests and the PBKDF2 work factor. Initializing a Phase 5 database creates this table and advances `PRAGMA user_version` to 2 without deleting existing customers, accounts, or transactions.
