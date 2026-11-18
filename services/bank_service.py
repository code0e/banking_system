
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

    # -------------------------
    # DEPOSIT OPERATIONS
    # -------------------------

    def deposit(
        self,
        account_number: str,
        amount: Decimal,
        customer_id: Optional[str] = None,
    ):
        """
        Deposit money into an account.

        The account model validates the amount and records
        the successful deposit in its transaction history.
        """

        account = self.get_account(
            account_number,
            customer_id,
        )

        account.deposit(amount)

        return account.transactions[-1]

    # -------------------------
    # WITHDRAWAL OPERATIONS
    # -------------------------

    def withdraw(
        self,
        account_number: str,
        amount: Decimal,
        customer_id: Optional[str] = None,
    ):
        """
        Withdraw money from an account.

        The account model enforces its own withdrawal rules,
        including savings minimum balances and current-account
        overdraft limits.
        """

        account = self.get_account(
            account_number,
            customer_id,
        )

        account.withdraw(amount)

        return account.transactions[-1]

    # -------------------------
    # TRANSACTION HISTORY
    # -------------------------

    def get_transaction_history(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ):
        """Retrieve a read-only snapshot of an account's transactions."""

        account = self.get_account(
            account_number,
            customer_id,
        )

        return account.transactions

    # -------------------------
    # ACCOUNT STATEMENTS
    # -------------------------

    def generate_statement(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ) -> str:
        """Generate a readable statement for an account."""

        account = self.get_account(
            account_number,
            customer_id,
        )

        lines = [
            "=" * 55,
            "                 LOGICBANK",
            "              ACCOUNT STATEMENT",
            "=" * 55,
            f"Customer: {account.owner.full_name}",
            f"Account Number: {account.account_number}",
            f"Account Type: {type(account).__name__}",
            "-" * 55,
            "TRANSACTION HISTORY",
            "-" * 55,
        ]

        transactions = account.transactions

        if not transactions:
            lines.append("No transactions recorded.")

        for transaction in transactions:
            timestamp = transaction.timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            transaction_type = (
                transaction.transaction_type.value
            )

            lines.append(
                f"{timestamp} | "
                f"{transaction_type:<12} | "
                f"NGN {transaction.amount:,.2f} | "
                f"Ref: {transaction.reference}"
            )

        lines.extend([
            "-" * 55,
            f"Available Balance: NGN {account.balance:,.2f}",
            "=" * 55,
            "          Thank you for banking with us.",
            "=" * 55,
        ])

        return "\n".join(lines)
