
import secrets
from decimal import Decimal
from typing import Optional

from exceptions import (
    AccountNotFoundError,
    AccountNumberGenerationError,
    AccountOwnershipError,
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
)
from models.customer import Customer
from models.savings_account import SavingsAccount
from models.current_account import CurrentAccount


class BankService:
    """
    Central service for managing LogicBank customers and accounts.

    Current implementation uses in-memory storage.
    SQLite persistence will be introduced in a later phase.
    """

    ACCOUNT_NUMBER_LENGTH = 10
    MAX_ACCOUNT_NUMBER_ATTEMPTS = 100

    def __init__(self):
        self._customers = {}
        self._customers_by_email = {}
        self._accounts = {}

    # -------------------------
    # CUSTOMER MANAGEMENT
    # -------------------------

    def register_customer(
        self,
        full_name: str,
        email: str,
        phone: str = "",
    ) -> Customer:
        """Register a new customer."""

        customer = Customer(
            full_name=full_name,
            email=email,
            phone=phone,
        )

        normalized_email = customer.email

        if normalized_email in self._customers_by_email:
            raise CustomerAlreadyExistsError(
                "A customer with this email already exists."
            )

        if customer.customer_id in self._customers:
            raise CustomerAlreadyExistsError(
                "This customer ID already exists."
            )

        self._customers[customer.customer_id] = customer
        self._customers_by_email[normalized_email] = customer.customer_id

        return customer

    def get_customer(self, customer_id: str) -> Customer:
        """Retrieve a customer using their unique ID."""

        customer = self._customers.get(customer_id)

        if customer is None:
            raise CustomerNotFoundError(
                "Customer could not be found."
            )

        return customer

    def get_customer_by_email(self, email: str) -> Customer:
        """Retrieve a customer using their email address."""

        if not isinstance(email, str):
            raise CustomerNotFoundError(
                "Customer could not be found."
            )

        customer_id = self._customers_by_email.get(
            email.strip().lower()
        )

        if customer_id is None:
            raise CustomerNotFoundError(
                "Customer could not be found."
            )

        return self._customers[customer_id]

    def list_customers(self):
        """Return a read-only snapshot of registered customers."""

        return tuple(self._customers.values())

    # -------------------------
    # ACCOUNT NUMBER GENERATION
    # -------------------------

    def _generate_account_number(self) -> str:
        """Generate a unique ten-digit account number."""

        for _ in range(self.MAX_ACCOUNT_NUMBER_ATTEMPTS):

            number = str(
                secrets.randbelow(9_000_000_000)
                + 1_000_000_000
            )

            if number not in self._accounts:
                return number

        raise AccountNumberGenerationError(
            "Unable to generate a unique account number."
        )

    # -------------------------
    # ACCOUNT CREATION
    # -------------------------

    def create_savings_account(
        self,
        customer_id: str,
        opening_balance=Decimal("1000.00"),
        minimum_balance=Decimal("1000.00"),
    ) -> SavingsAccount:
        """Create a savings account for a registered customer."""

        customer = self.get_customer(customer_id)

        account_number = self._generate_account_number()

        account = SavingsAccount(
            owner=customer,
            account_number=account_number,
            opening_balance=opening_balance,
            minimum_balance=minimum_balance,
        )

        self._accounts[account_number] = account

        return account

    def create_current_account(
        self,
        customer_id: str,
        opening_balance=Decimal("0.00"),
        overdraft_limit=Decimal("0.00"),
    ) -> CurrentAccount:
        """Create a current account for a registered customer."""

        customer = self.get_customer(customer_id)

        account_number = self._generate_account_number()

        account = CurrentAccount(
            owner=customer,
            account_number=account_number,
            opening_balance=opening_balance,
            overdraft_limit=overdraft_limit,
        )

        self._accounts[account_number] = account

        return account

    # -------------------------
    # ACCOUNT MANAGEMENT
    # -------------------------

    def get_account(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ):
        """
        Retrieve an account.

        If customer_id is supplied, ownership is verified
        before the account is returned.
        """

        account = self._accounts.get(account_number)

        if account is None:
            raise AccountNotFoundError(
                "Account could not be found."
            )

        if (
            customer_id is not None
            and account.owner.customer_id != customer_id
        ):
            raise AccountOwnershipError(
                "You are not authorized to access this account."
            )

        return account

    def get_customer_accounts(self, customer_id: str):
        """Return all accounts belonging to a customer."""

        self.get_customer(customer_id)

        customer_accounts = [
            account
            for account in self._accounts.values()
            if account.owner.customer_id == customer_id
        ]

        return tuple(customer_accounts)

    def get_total_customer_accounts(self, customer_id: str) -> int:
        """Return the number of accounts owned by a customer."""

        return len(self.get_customer_accounts(customer_id))

    def get_total_customers(self) -> int:
        """Return the number of registered customers."""

        return len(self._customers)

    def get_total_accounts(self) -> int:
        """Return the number of registered accounts."""

        return len(self._accounts)
