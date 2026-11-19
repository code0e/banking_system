"""Persistence operations for account transaction history."""
import sqlite3
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from database.connection import Database
from models.transaction import Transaction, TransactionType
from exceptions import AccountNotFoundError


class TransactionRepository:
    """Save and retrieve immutable transaction records."""
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _kobo(amount: Decimal) -> int:
        value = Decimal(str(amount))
        if value != value.quantize(Decimal('0.01')):
            raise ValueError('Transaction amount must have two decimal places or fewer.')
        return int(value * 100)

    def save(self, account_number: str, transaction: Transaction, connection: sqlite3.Connection | None = None) -> None:
        values = (str(transaction.reference), account_number, transaction.transaction_type.value, self._kobo(transaction.amount), transaction.description, transaction.timestamp.isoformat())
        sql = 'INSERT INTO transactions(reference, account_number, transaction_type, amount_kobo, description, timestamp) VALUES (?, ?, ?, ?, ?, ?)'
        if connection is not None:
            connection.execute(sql, values)
        else:
            try:
                with self.database.transaction() as db:
                    db.execute(sql, values)
            except sqlite3.IntegrityError as error:
                raise AccountNotFoundError('Account could not be found for this transaction.') from error

    def list_for_account(self, account_number: str) -> tuple[Transaction, ...]:
        with self.database.connect() as connection:
            rows = connection.execute('SELECT * FROM transactions WHERE account_number = ? ORDER BY transaction_id', (account_number,)).fetchall()
        return tuple(Transaction(TransactionType(row['transaction_type']), Decimal(row['amount_kobo']) / 100, row['description'], row['reference'], datetime.fromisoformat(row['timestamp'])) for row in rows)

    def list_by_reference(self, reference: str) -> tuple[tuple[str, Transaction], ...]:
        with self.database.connect() as connection:
            rows = connection.execute('SELECT account_number, * FROM transactions WHERE reference = ? ORDER BY transaction_id', (str(reference),)).fetchall()
        return tuple((row['account_number'], Transaction(TransactionType(row['transaction_type']), Decimal(row['amount_kobo']) / 100, row['description'], row['reference'], datetime.fromisoformat(row['timestamp']))) for row in rows)
