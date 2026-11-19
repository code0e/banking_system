"""SQLite schema for the banking system.

Schema version 2 adds a separate credential table. Passwords are never stored
in plaintext and are not added to the customer profile table.
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    phone TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
    account_number TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    account_type TEXT NOT NULL CHECK (account_type IN ('SAVINGS', 'CURRENT')),
    balance_kobo INTEGER NOT NULL,
    minimum_balance_kobo INTEGER NOT NULL DEFAULT 0,
    overdraft_limit_kobo INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (minimum_balance_kobo >= 0),
    CHECK (overdraft_limit_kobo >= 0),
    CHECK (account_type != 'SAVINGS' OR overdraft_limit_kobo = 0),
    CHECK (account_type != 'CURRENT' OR minimum_balance_kobo = 0)
);
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference TEXT NOT NULL,
    account_number TEXT NOT NULL REFERENCES accounts(account_number) ON DELETE RESTRICT,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('DEPOSIT','WITHDRAWAL','TRANSFER_IN','TRANSFER_OUT')),
    amount_kobo INTEGER NOT NULL CHECK (amount_kobo > 0),
    description TEXT NOT NULL DEFAULT '',
    timestamp TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS customer_credentials (
    customer_id TEXT PRIMARY KEY REFERENCES customers(customer_id) ON DELETE CASCADE,
    password_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    iterations INTEGER NOT NULL CHECK (iterations >= 100000),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_accounts_customer ON accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_number, transaction_id);
CREATE INDEX IF NOT EXISTS idx_transactions_reference ON transactions(reference);
"""
