"""Tests for database connection, schema, and transaction guarantees."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from database import Database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp.name) / 'test.db')
        self.database.initialize()

    def tearDown(self):
        self.temp.cleanup()

    def test_schema_is_initialized(self):
        with self.database.connect() as connection:
            names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({'customers', 'accounts', 'transactions', 'customer_credentials'}.issubset(names))

    def test_foreign_keys_are_enabled(self):
        with self.database.connect() as connection:
            self.assertEqual(connection.execute('PRAGMA foreign_keys').fetchone()[0], 1)

    def test_schema_initialization_is_idempotent(self):
        self.database.initialize()
        with self.database.connect() as connection:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 2)

    def test_phase_five_database_migrates_without_losing_customer_data(self):
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO customers VALUES (?, ?, ?, ?, ?)",
                ("legacy-customer", "Legacy Customer", "legacy@example.com", "", "2026-01-01T00:00:00+00:00"),
            )
            connection.execute("DROP TABLE customer_credentials")
            connection.execute("PRAGMA user_version = 1")

        self.database.initialize()

        with self.database.connect() as connection:
            customer = connection.execute(
                "SELECT full_name FROM customers WHERE customer_id = ?",
                ("legacy-customer",),
            ).fetchone()
            credential_table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'customer_credentials'"
            ).fetchone()
            version = connection.execute("PRAGMA user_version").fetchone()[0]

        self.assertEqual(customer["full_name"], "Legacy Customer")
        self.assertIsNotNone(credential_table)
        self.assertEqual(version, 2)

    def test_transaction_commits(self):
        with self.database.transaction() as connection:
            connection.execute("INSERT INTO customers(customer_id, full_name, email, phone, created_at) VALUES ('id-1','Ada','ada@test.com','','2026-01-01T00:00:00+00:00')")
        with self.database.connect() as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM customers').fetchone()[0], 1)

    def test_transaction_rolls_back(self):
        with self.assertRaises(RuntimeError):
            with self.database.transaction() as connection:
                connection.execute("INSERT INTO customers(customer_id, full_name, email, phone, created_at) VALUES ('id-1','Ada','ada@test.com','','2026-01-01T00:00:00+00:00')")
                raise RuntimeError('rollback')
        with self.database.connect() as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM customers').fetchone()[0], 0)

    def test_unique_customer_email_constraint(self):
        with self.database.transaction() as connection:
            connection.execute("INSERT INTO customers VALUES ('1','Ada','ada@test.com','','2026-01-01')")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.transaction() as connection:
                connection.execute("INSERT INTO customers VALUES ('2','Grace','ADA@test.com','','2026-01-01')")

    def test_invalid_account_type_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.transaction() as connection:
                connection.execute("INSERT INTO accounts VALUES ('123','missing','INVALID',0,0,0,CURRENT_TIMESTAMP)")

    def test_transaction_amount_must_be_positive(self):
        with self.database.transaction() as connection:
            connection.execute("INSERT INTO customers VALUES ('c1','Ada','ada@test.com','','2026-01-01')")
            connection.execute("INSERT INTO accounts(account_number,customer_id,account_type,balance_kobo) VALUES ('123','c1','CURRENT',0)")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.database.transaction() as connection:
                connection.execute("INSERT INTO transactions(reference,account_number,transaction_type,amount_kobo,timestamp) VALUES ('r','123','DEPOSIT',0,'2026-01-01')")

    def test_parameterized_insert_handles_apostrophes(self):
        with self.database.transaction() as connection:
            connection.execute('INSERT INTO customers VALUES (?, ?, ?, ?, ?)', ('c1', "O'Neil", 'oneil@test.com', '', '2026-01-01'))
        with self.database.connect() as connection:
            self.assertEqual(connection.execute('SELECT full_name FROM customers').fetchone()[0], "O'Neil")


if __name__ == '__main__':
    unittest.main()
