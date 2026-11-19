"""Persistence operations for savings and current accounts."""
import sqlite3
from decimal import Decimal
from exceptions import AccountError, AccountNotFoundError
from database.connection import Database
from models.account import BankAccount
from models.current_account import CurrentAccount
from models.savings_account import SavingsAccount
from repositories.customer_repository import CustomerRepository

CENT = Decimal('0.01')


class AccountRepository:
    """Store accounts with exact integer-kobo monetary values."""
    def __init__(self, database: Database, customers: CustomerRepository | None = None) -> None:
        self.database = database
        self.customers = customers or CustomerRepository(database)

    @staticmethod
    def _to_kobo(amount: Decimal) -> int:
        value = Decimal(str(amount))
        if value != value.quantize(CENT):
            raise AccountError('Account money must have at most two decimal places.')
        return int(value * 100)

    @staticmethod
    def _from_kobo(amount: int) -> Decimal:
        return Decimal(amount) / 100

    def save(self, account: BankAccount) -> BankAccount:
        if isinstance(account, SavingsAccount):
            kind, minimum, overdraft = 'SAVINGS', self._to_kobo(account.minimum_balance), 0
        elif isinstance(account, CurrentAccount):
            kind, minimum, overdraft = 'CURRENT', 0, self._to_kobo(account.overdraft_limit)
        else:
            raise AccountError('Unsupported account type.')
        with self.database.transaction() as connection:
            connection.execute('INSERT INTO accounts(account_number, customer_id, account_type, balance_kobo, minimum_balance_kobo, overdraft_limit_kobo) VALUES (?, ?, ?, ?, ?, ?)', (account.account_number, account.owner.customer_id, kind, self._to_kobo(account.balance), minimum, overdraft))
        return account

    def _from_row(self, row: sqlite3.Row) -> BankAccount:
        owner = self.customers.get_by_id(row['customer_id'])
        if owner is None:
            raise AccountError('The account owner does not exist.')
        balance = self._from_kobo(row['balance_kobo'])
        if row['account_type'] == 'SAVINGS':
            account = SavingsAccount(owner, row['account_number'], balance, self._from_kobo(row['minimum_balance_kobo']))
        else:
            account = CurrentAccount(owner, row['account_number'], max(balance, Decimal('0.00')), self._from_kobo(row['overdraft_limit_kobo']))
            if balance < 0:
                account._restore_persisted_balance(balance)
        return account

    def get_by_number(self, account_number: str) -> BankAccount | None:
        with self.database.connect() as connection:
            row = connection.execute('SELECT * FROM accounts WHERE account_number = ?', (account_number,)).fetchone()
        if row is None:
            return None
        account = self._from_row(row)
        account._restore_persisted_transactions(self._load_transactions(account_number))
        return account

    def _load_transactions(self, account_number: str):
        from repositories.transaction_repository import TransactionRepository
        return TransactionRepository(self.database).list_for_account(account_number)

    def list_by_customer(self, customer_id: str) -> tuple[BankAccount, ...]:
        with self.database.connect() as connection:
            rows = connection.execute('SELECT account_number FROM accounts WHERE customer_id = ? ORDER BY account_number', (customer_id,)).fetchall()
        return tuple(self.get_by_number(row['account_number']) for row in rows)

    def list_all(self) -> tuple[BankAccount, ...]:
        with self.database.connect() as connection:
            rows = connection.execute('SELECT account_number FROM accounts ORDER BY account_number').fetchall()
        return tuple(self.get_by_number(row['account_number']) for row in rows)

    def update_balance(self, account_number: str, balance: Decimal, connection: sqlite3.Connection | None = None) -> None:
        values = (self._to_kobo(balance), account_number)
        if connection is not None:
            cursor = connection.execute('UPDATE accounts SET balance_kobo = ? WHERE account_number = ?', values)
            if cursor.rowcount != 1:
                raise AccountNotFoundError('Account could not be found.')
            return
        with self.database.transaction() as db:
            self.update_balance(account_number, balance, db)

    def exists(self, account_number: str) -> bool:
        with self.database.connect() as connection:
            return connection.execute('SELECT 1 FROM accounts WHERE account_number = ?', (account_number,)).fetchone() is not None

    def count_by_customer(self, customer_id: str) -> int:
        with self.database.connect() as connection:
            return connection.execute('SELECT COUNT(*) FROM accounts WHERE customer_id = ?', (customer_id,)).fetchone()[0]
