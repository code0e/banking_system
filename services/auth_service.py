"""Customer registration, login, password changes, and session management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import secrets

from database.connection import Database
from exceptions import (
    CustomerAlreadyExistsError,
    InvalidCredentialsError,
    SessionNotFoundError,
)
from models.customer import Customer
from models.current_account import CurrentAccount
from models.savings_account import SavingsAccount
from models.transaction import Transaction
from repositories.user_repository import UserRepository
from repositories.customer_repository import CustomerRepository
from services.bank_service import BankService
from utils.security import PasswordHasher


@dataclass(frozen=True)
class AuthSession:
    """An in-memory authenticated customer session."""

    token: str
    customer: Customer
    created_at: datetime
    expires_at: datetime


class AuthService:
    """Manage customer identities and short-lived in-memory sessions.

    Credential data is stored in SQLite. Session tokens are random bearer
    tokens held only in this service's memory and are invalidated on logout or
    service restart. This is suitable for the educational CLI, not a
    distributed production authentication system.
    """

    def __init__(
        self,
        database: Database,
        bank_service: BankService | None = None,
        session_lifetime: timedelta = timedelta(hours=1),
    ) -> None:
        if session_lifetime.total_seconds() <= 0:
            raise ValueError("Session lifetime must be positive.")
        self.database = database
        self.database.initialize()
        self.user_repository = UserRepository(database)
        self.customer_repository = CustomerRepository(database)
        self.bank_service = bank_service or BankService(database)
        if self.bank_service.database is None:
            raise ValueError("AuthService requires a database-backed BankService.")
        if self.bank_service.database.path != database.path:
            raise ValueError("AuthService and BankService must share one database.")
        self.session_lifetime = session_lifetime
        self._sessions: dict[str, AuthSession] = {}

    def register(
        self, full_name: str, email: str, password: str, phone: str = ""
    ) -> Customer:
        """Register a customer and credential atomically."""
        customer = Customer(full_name=full_name, email=email, phone=phone)
        if self.user_repository.get_credentials_by_email(customer.email):
            raise CustomerAlreadyExistsError(
                "A customer with this email already exists."
            )
        salt, digest, iterations = PasswordHasher.hash_password(password)
        self.user_repository.create_customer(customer, salt, digest, iterations)
        self.bank_service.adopt_customer(customer)
        return customer

    def enroll_existing_customer(
        self, customer_id: str, password: str
    ) -> Customer:
        """Attach a first password to a legacy Phase 5 customer.

        This is a trusted migration/admin operation, not a public sign-up
        endpoint. Verify the customer's identity before invoking it.
        """
        customer = self.customer_repository.get_by_id(customer_id)
        if customer is None:
            raise InvalidCredentialsError("Customer could not be verified.")
        salt, digest, iterations = PasswordHasher.hash_password(password)
        self.user_repository.add_credentials_for_existing_customer(
            customer_id, salt, digest, iterations
        )
        self.bank_service.adopt_customer(customer)
        return customer

    def login(self, email: str, password: str) -> AuthSession:
        """Authenticate a customer and issue a random expiring session token."""
        if not isinstance(email, str) or not isinstance(password, str):
            raise InvalidCredentialsError("Invalid email or password.")
        record = self.user_repository.get_credentials_by_email(email)
        if record is None or not PasswordHasher.verify_password(
            password,
            str(record["password_salt"]),
            str(record["password_hash"]),
            int(record["iterations"]),
        ):
            raise InvalidCredentialsError("Invalid email or password.")

        customer = Customer(
            full_name=str(record["full_name"]),
            email=str(record["email"]),
            phone=str(record["phone"]),
            customer_id=str(record["customer_id"]),
            created_at=datetime.fromisoformat(str(record["created_at"])),
        )
        self.bank_service.adopt_customer(customer)
        now = datetime.now(timezone.utc)
        session = AuthSession(
            token=secrets.token_urlsafe(32),
            customer=customer,
            created_at=now,
            expires_at=now + self.session_lifetime,
        )
        self._sessions[session.token] = session
        return session

    def require_customer(self, session_token: str) -> Customer:
        """Return the session customer or reject invalid/expired tokens."""
        if not isinstance(session_token, str) or not session_token:
            raise SessionNotFoundError("Your session is invalid. Please log in.")
        session = self._sessions.get(session_token)
        if session is None:
            raise SessionNotFoundError("Your session is invalid. Please log in.")
        if datetime.now(timezone.utc) >= session.expires_at:
            self._sessions.pop(session_token, None)
            raise SessionNotFoundError("Your session has expired. Please log in.")
        return session.customer

    def logout(self, session_token: str) -> None:
        """Invalidate an active session token."""
        if (
            not isinstance(session_token, str)
            or not session_token
            or self._sessions.pop(session_token, None) is None
        ):
            raise SessionNotFoundError("Your session is invalid or already logged out.")

    def change_password(
        self, session_token: str, current_password: str, new_password: str
    ) -> None:
        """Verify the current password and persist a new salted hash."""
        customer = self.require_customer(session_token)
        record = self.user_repository.get_credentials_by_email(customer.email)
        if record is None or not PasswordHasher.verify_password(
            current_password,
            str(record["password_salt"]),
            str(record["password_hash"]),
            int(record["iterations"]),
        ):
            raise InvalidCredentialsError("Current password is incorrect.")
        salt, digest, iterations = PasswordHasher.hash_password(new_password)
        self.user_repository.update_password(
            customer.customer_id, salt, digest, iterations
        )
        # Revoke all sessions for this customer after a credential change.
        self._sessions = {
            token: session for token, session in self._sessions.items()
            if session.customer.customer_id != customer.customer_id
        }

    def get_customer_accounts(
        self, session_token: str
    ) -> tuple[SavingsAccount | CurrentAccount, ...]:
        """List only the authenticated customer's accounts."""
        customer = self.require_customer(session_token)
        return self.bank_service.get_customer_accounts(customer.customer_id)

    def get_account(
        self, session_token: str, account_number: str
    ) -> SavingsAccount | CurrentAccount:
        """Retrieve an account only when it belongs to the session customer."""
        customer = self.require_customer(session_token)
        return self.bank_service.get_account(account_number, customer.customer_id)

    def deposit(
        self, session_token: str, account_number: str, amount: Decimal
    ) -> Transaction:
        """Perform a deposit on an account owned by the session customer."""
        customer = self.require_customer(session_token)
        return self.bank_service.deposit(
            account_number, amount, customer_id=customer.customer_id
        )

    def withdraw(
        self, session_token: str, account_number: str, amount: Decimal
    ) -> Transaction:
        """Perform a withdrawal on an account owned by the session customer."""
        customer = self.require_customer(session_token)
        return self.bank_service.withdraw(
            account_number, amount, customer_id=customer.customer_id
        )

    def transfer(
        self, session_token: str, sender_account_number: str,
        recipient_account_number: str, amount: Decimal,
    ) -> tuple[Transaction, Transaction]:
        """Transfer from an owned sender account to any valid recipient."""
        customer = self.require_customer(session_token)
        return self.bank_service.transfer(
            sender_account_number, recipient_account_number, amount,
            customer_id=customer.customer_id,
        )

    def get_transaction_history(
        self, session_token: str, account_number: str
    ) -> tuple[Transaction, ...]:
        """Read transaction history for an account owned by the customer."""
        customer = self.require_customer(session_token)
        return self.bank_service.get_transaction_history(
            account_number, customer_id=customer.customer_id
        )

    def generate_statement(self, session_token: str, account_number: str) -> str:
        """Generate a statement for an account owned by the customer."""
        customer = self.require_customer(session_token)
        return self.bank_service.generate_statement(
            account_number, customer_id=customer.customer_id
        )

    def active_session_count(self) -> int:
        """Return the number of currently unexpired in-memory sessions."""
        now = datetime.now(timezone.utc)
        expired = [
            token for token, session in self._sessions.items()
            if now >= session.expires_at
        ]
        for token in expired:
            self._sessions.pop(token, None)
        return len(self._sessions)
