"""Persistence operations for customers."""
import sqlite3
from datetime import datetime
from models.customer import Customer
from exceptions import CustomerAlreadyExistsError
from database.connection import Database


class CustomerRepository:
    """Store and retrieve customer records."""
    def __init__(self, database: Database) -> None:
        self.database = database

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Customer:
        return Customer(row['full_name'], row['email'], row['phone'], row['customer_id'], datetime.fromisoformat(row['created_at']))

    def save(self, customer: Customer) -> Customer:
        try:
            with self.database.transaction() as connection:
                connection.execute('INSERT INTO customers(customer_id, full_name, email, phone, created_at) VALUES (?, ?, ?, ?, ?)', (customer.customer_id, customer.full_name, customer.email, customer.phone, customer.created_at.isoformat()))
        except sqlite3.IntegrityError as error:
            raise CustomerAlreadyExistsError('A customer with this ID or email already exists.') from error
        return customer

    def get_by_id(self, customer_id: str) -> Customer | None:
        with self.database.connect() as connection:
            row = connection.execute('SELECT * FROM customers WHERE customer_id = ?', (customer_id,)).fetchone()
        return self._from_row(row) if row else None

    def get_by_email(self, email: str) -> Customer | None:
        with self.database.connect() as connection:
            row = connection.execute('SELECT * FROM customers WHERE email = ? COLLATE NOCASE', (email.strip(),)).fetchone()
        return self._from_row(row) if row else None

    def list_all(self) -> tuple[Customer, ...]:
        with self.database.connect() as connection:
            rows = connection.execute('SELECT * FROM customers ORDER BY created_at, customer_id').fetchall()
        return tuple(self._from_row(row) for row in rows)

    def exists_by_email(self, email: str) -> bool:
        return self.get_by_email(email) is not None
