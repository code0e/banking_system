"""Atomic persistence for customer profiles and password credentials."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from database.connection import Database
from exceptions import CustomerAlreadyExistsError, CustomerNotFoundError
from models.customer import Customer


class UserRepository:
    """Persist customers and their authentication credentials separately."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def create_customer(
        self,
        customer: Customer,
        salt_hex: str,
        password_hash_hex: str,
        iterations: int,
    ) -> Customer:
        """Insert a customer and credential in one database transaction."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """INSERT INTO customers
                    (customer_id, full_name, email, phone, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (customer.customer_id, customer.full_name, customer.email,
                     customer.phone, customer.created_at.isoformat()),
                )
                connection.execute(
                    """INSERT INTO customer_credentials
                    (customer_id, password_salt, password_hash, iterations,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (customer.customer_id, salt_hex, password_hash_hex,
                     iterations, now, now),
                )
        except sqlite3.IntegrityError as error:
            raise CustomerAlreadyExistsError(
                "A customer with this email or ID already exists."
            ) from error
        return customer

    def add_credentials_for_existing_customer(
        self, customer_id: str, salt_hex: str,
        password_hash_hex: str, iterations: int,
    ) -> None:
        """Attach initial credentials to a legacy customer without a login.

        This operation is intended for a trusted, administrator-controlled
        migration process after the customer's identity has been verified.
        It must not be exposed as an unauthenticated public registration flow.
        """
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.database.transaction() as connection:
                connection.execute(
                    """INSERT INTO customer_credentials
                    (customer_id, password_salt, password_hash, iterations,
                     created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (customer_id, salt_hex, password_hash_hex, iterations,
                     now, now),
                )
        except sqlite3.IntegrityError as error:
            raise CustomerNotFoundError(
                "Customer does not exist or already has login credentials."
            ) from error

    def get_credentials_by_email(self, email: str) -> dict[str, object] | None:
        """Return a customer profile and credential row for an email."""
        with self.database.connect() as connection:
            row = connection.execute(
                """SELECT c.customer_id, c.full_name, c.email, c.phone,
                          c.created_at, cr.password_salt, cr.password_hash,
                          cr.iterations
                   FROM customers AS c
                   JOIN customer_credentials AS cr
                     ON cr.customer_id = c.customer_id
                   WHERE c.email = ? COLLATE NOCASE""",
                (email.strip(),),
            ).fetchone()
        return dict(row) if row else None

    def has_credentials(self, customer_id: str) -> bool:
        """Return whether a customer has a credential record."""
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM customer_credentials WHERE customer_id = ?",
                (customer_id,),
            ).fetchone()
        return row is not None

    def update_password(
        self, customer_id: str, salt_hex: str,
        password_hash_hex: str, iterations: int,
    ) -> None:
        """Replace a customer's password hash without storing plaintext."""
        now = datetime.now(timezone.utc).isoformat()
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """UPDATE customer_credentials
                   SET password_salt = ?, password_hash = ?, iterations = ?,
                       updated_at = ?
                   WHERE customer_id = ?""",
                (salt_hex, password_hash_hex, iterations, now, customer_id),
            )
            if cursor.rowcount != 1:
                raise CustomerNotFoundError(
                    "Customer authentication record could not be found."
                )

    def delete_credentials(self, customer_id: str) -> None:
        """Delete credentials for a customer (used by account closure later)."""
        with self.database.transaction() as connection:
            connection.execute(
                "DELETE FROM customer_credentials WHERE customer_id = ?",
                (customer_id,),
            )
