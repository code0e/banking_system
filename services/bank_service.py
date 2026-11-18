"""Application service for LogicBank's in-memory banking operations.

The service coordinates customer registration, account creation, ownership
checks, deposits, withdrawals, transaction history, and statement generation.

Storage is currently held in Python dictionaries. Data therefore exists only
for the lifetime of the BankService instance; SQLite persistence, customer
authentication, and money transfers are separate future implementation phases.
"""

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
from models.transaction import Transaction


class BankService:
    """Coordinate LogicBank's customer and account operations.

    ``BankService`` acts as the application-facing layer between a user
    interface and the domain models. It delegates monetary rules to account
    objects rather than duplicating those rules here.

    Notes:
        This version uses in-memory dictionaries. Creating a new service
        instance starts with an empty bank.
    """

    ACCOUNT_NUMBER_LENGTH = 10
    MAX_ACCOUNT_NUMBER_ATTEMPTS = 100

    def __init__(self) -> None:
        """Create empty in-memory customer and account registries."""
        self._customers: dict[str, Customer] = {}
        self._customers_by_email: dict[str, str] = {}
        self._accounts: dict[str, SavingsAccount | CurrentAccount] = {}

    # CUSTOMER MANAGEMENT

    def register_customer(
        self,
        full_name: str,
        email: str,
        phone: str = "",
    ) -> Customer:
        """Validate and register a new customer.

        Email addresses are normalized by the Customer model before they are
        checked for duplicates.
        """
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
        """Return a customer by unique ID or raise CustomerNotFoundError."""
        customer = self._customers.get(customer_id)

        if customer is None:
            raise CustomerNotFoundError(
                "Customer could not be found."
            )

        return customer

    def get_customer_by_email(self, email: str) -> Customer:
        """Return a customer by case-insensitive email address."""
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

    def list_customers(self) -> tuple[Customer, ...]:
        """Return a tuple snapshot of all registered customers."""
        return tuple(self._customers.values())

    # ACCOUNT NUMBER GENERATION

    def _generate_account_number(self) -> str:
        """Generate an unused ten-digit account number.

        A bounded retry count prevents an endless loop if the account-number
        space ever becomes unexpectedly crowded.
        """
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

    # ACCOUNT CREATION

    def create_savings_account(
        self,
        customer_id: str,
        opening_balance: Decimal = Decimal("1000.00"),
        minimum_balance: Decimal = Decimal("1000.00"),
    ) -> SavingsAccount:
        """Create and register a savings account for an existing customer."""
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
        opening_balance: Decimal = Decimal("0.00"),
        overdraft_limit: Decimal = Decimal("0.00"),
    ) -> CurrentAccount:
        """Create and register a current account for an existing customer."""
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

    # ACCOUNT MANAGEMENT

    def get_account(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ) -> SavingsAccount | CurrentAccount:
        """Retrieve an account and optionally verify its owner.

        Args:
            account_number: Account to retrieve.
            customer_id: When supplied, the account must belong to this
                customer. Omitting it is intended for trusted internal use.

        Raises:
            AccountNotFoundError: If the account number is unknown.
            AccountOwnershipError: If the supplied customer does not own it.
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

    def get_customer_accounts(
        self,
        customer_id: str,
    ) -> tuple[SavingsAccount | CurrentAccount, ...]:
        """Return all accounts owned by a registered customer."""
        self.get_customer(customer_id)

        customer_accounts = [
            account
            for account in self._accounts.values()
            if account.owner.customer_id == customer_id
        ]

        return tuple(customer_accounts)

    def get_total_customer_accounts(self, customer_id: str) -> int:
        """Return the number of accounts belonging to one customer."""
        return len(self.get_customer_accounts(customer_id))

    def get_total_customers(self) -> int:
        """Return the number of registered customers."""
        return len(self._customers)

    def get_total_accounts(self) -> int:
        """Return the number of registered accounts."""
        return len(self._accounts)

    # DEPOSIT OPERATIONS

    def deposit(
        self,
        account_number: str,
        amount: Decimal,
        customer_id: Optional[str] = None,
    ) -> Transaction:
        """Deposit money into an account after an optional ownership check.

        The account model validates the amount, updates the balance, and
        creates the transaction record.
        """
        account = self.get_account(
            account_number,
            customer_id,
        )

        return account.deposit(amount)

    # WITHDRAWAL OPERATIONS

    def withdraw(
        self,
        account_number: str,
        amount: Decimal,
        customer_id: Optional[str] = None,
    ) -> Transaction:
        """Withdraw money after an optional ownership check.

        The concrete account model enforces the applicable minimum-balance or
        overdraft rule.
        """
        account = self.get_account(
            account_number,
            customer_id,
        )

        return account.withdraw(amount)

    # TRANSACTION HISTORY

    def get_transaction_history(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ) -> tuple[Transaction, ...]:
        """Return the account's read-only transaction-history snapshot."""
        account = self.get_account(
            account_number,
            customer_id,
        )

        return account.transactions

    # ACCOUNT STATEMENTS

    def generate_statement(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ) -> str:
        """Build a printable text statement for an account.

        The statement includes account details, recorded transactions,
        transaction references, timestamps, and the current available balance.
        """
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

            transaction_type = transaction.transaction_type.value

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
