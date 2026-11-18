"""Application service for LogicBank's in-memory banking operations.

BankService coordinates customers, accounts, ownership checks, and banking
operations. Account-specific financial rules remain in the account models.
"""

import secrets
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from exceptions import (
    AccountNotFoundError,
    AccountNumberGenerationError,
    AccountOwnershipError,
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
    ValidationError,
)
from models.customer import Customer
from models.savings_account import SavingsAccount
from models.current_account import CurrentAccount
from models.transaction import Transaction, TransactionType
from utils.validators import to_money


class BankService:
    """Coordinate LogicBank customer and account operations.

    The current storage layer uses in-memory dictionaries. Records are lost
    when the service process ends; persistent storage is a later project phase.
    """

    ACCOUNT_NUMBER_LENGTH = 10
    MAX_ACCOUNT_NUMBER_ATTEMPTS = 100

    def __init__(self) -> None:
        """Create empty in-memory customer and account registries."""
        self._customers: dict[str, Customer] = {}
        self._customers_by_email: dict[str, str] = {}
        self._accounts: dict[str, SavingsAccount | CurrentAccount] = {}

    def register_customer(
        self,
        full_name: str,
        email: str,
        phone: str = "",
    ) -> Customer:
        """Register a customer after validating uniqueness."""
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
        """Retrieve a customer by ID."""
        customer = self._customers.get(customer_id)
        if customer is None:
            raise CustomerNotFoundError(
                "Customer could not be found."
            )
        return customer

    def get_customer_by_email(self, email: str) -> Customer:
        """Retrieve a customer using a case-insensitive email lookup."""
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
        """Return a read-only snapshot of registered customers."""
        return tuple(self._customers.values())

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

    def create_savings_account(
        self,
        customer_id: str,
        opening_balance: Decimal = Decimal("1000.00"),
        minimum_balance: Decimal = Decimal("1000.00"),
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
        opening_balance: Decimal = Decimal("0.00"),
        overdraft_limit: Decimal = Decimal("0.00"),
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

    def get_account(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ) -> SavingsAccount | CurrentAccount:
        """Retrieve an account and optionally verify its ownership."""
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
        return tuple(
            account
            for account in self._accounts.values()
            if account.owner.customer_id == customer_id
        )

    def get_total_customer_accounts(self, customer_id: str) -> int:
        """Return the number of accounts owned by a customer."""
        return len(self.get_customer_accounts(customer_id))

    def get_total_customers(self) -> int:
        """Return the number of registered customers."""
        return len(self._customers)

    def get_total_accounts(self) -> int:
        """Return the number of registered accounts."""
        return len(self._accounts)

    def deposit(
        self,
        account_number: str,
        amount: Decimal,
        customer_id: Optional[str] = None,
    ) -> Transaction:
        """Deposit money after an optional ownership check."""
        account = self.get_account(account_number, customer_id)
        return account.deposit(amount)

    def withdraw(
        self,
        account_number: str,
        amount: Decimal,
        customer_id: Optional[str] = None,
    ) -> Transaction:
        """Withdraw money after an optional ownership check."""
        account = self.get_account(account_number, customer_id)
        return account.withdraw(amount)

    def transfer(
        self,
        sender_account_number: str,
        recipient_account_number: str,
        amount: Decimal,
        customer_id: Optional[str] = None,
    ) -> tuple[Transaction, Transaction]:
        """Transfer funds between two accounts as one atomic operation.

        The optional ``customer_id`` authenticates ownership of the sender
        account. The recipient may belong to the same or another customer.

        Both transaction records share one reference so the transfer can be
        traced from either account. If applying either record raises an
        exception, both account balances and transaction histories are
        restored to their pre-transfer snapshots.

        Returns:
            A pair containing ``(transfer_out, transfer_in)``.

        Raises:
            AccountNotFoundError: If either account does not exist.
            AccountOwnershipError: If the caller does not own the sender.
            ValidationError: If both account numbers are the same.
            InvalidAmountError: If the transfer amount is invalid.
            MinimumBalanceError: If a savings account's minimum would be
                breached.
            InsufficientFundsError: If the sender lacks permitted funds.
        """
        sender = self.get_account(
            sender_account_number,
            customer_id,
        )
        recipient = self.get_account(recipient_account_number)

        if sender.account_number == recipient.account_number:
            raise ValidationError(
                "You cannot transfer money to the same account."
            )

        # Validate the amount and the sender's account-specific withdrawal
        # policy before changing either account.
        amount = to_money(amount)
        amount = sender._validate_transfer_out(amount)

        # Both entries share a reference, linking the debit and credit.
        transfer_reference = uuid4()
        transfer_out = Transaction(
            transaction_type=TransactionType.TRANSFER_OUT,
            amount=amount,
            description=(
                f"Transfer to account {recipient.account_number}"
            ),
            reference=transfer_reference,
        )
        transfer_in = Transaction(
            transaction_type=TransactionType.TRANSFER_IN,
            amount=amount,
            description=(
                f"Transfer from account {sender.account_number}"
            ),
            reference=transfer_reference,
        )

        sender_snapshot = sender._snapshot_transfer_state()
        recipient_snapshot = recipient._snapshot_transfer_state()

        try:
            sender._apply_transfer(transfer_out)
            recipient._apply_transfer(transfer_in)
        except Exception:
            # Restore both sides, including any entry appended before failure.
            sender._restore_transfer_state(sender_snapshot)
            recipient._restore_transfer_state(recipient_snapshot)
            raise

        return transfer_out, transfer_in

    def get_transaction_history(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ) -> tuple[Transaction, ...]:
        """Return an immutable snapshot of an account's transactions."""
        account = self.get_account(account_number, customer_id)
        return account.transactions

    def generate_statement(
        self,
        account_number: str,
        customer_id: Optional[str] = None,
    ) -> str:
        """Generate a readable text statement for an account."""
        account = self.get_account(account_number, customer_id)
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
