"""Core abstract account model for LogicBank.

Concrete account types inherit shared balance and transaction behaviour while
implementing their own withdrawal and transfer-out policies.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

from exceptions import (
    AccountError,
    InsufficientFundsError,
    MinimumBalanceError,
)
from models.customer import Customer
from models.transaction import Transaction, TransactionType
from utils.validators import to_money, validate_non_empty


class BankAccount(ABC):
    """Abstract base class for customer-owned bank accounts.

    The balance and transaction history are encapsulated. Public callers can
    inspect the balance and obtain an immutable history snapshot. Internal
    transfer helpers allow BankService to apply and roll back paired entries.
    """

    def __init__(
        self,
        owner: Customer,
        account_number: str,
        opening_balance: Decimal = Decimal("0.00"),
    ) -> None:
        """Create an account with a validated owner, number, and balance."""
        if not isinstance(owner, Customer):
            raise AccountError("A valid customer is required.")

        self.owner = owner
        self.account_number = validate_non_empty(
            account_number, "Account number"
        )
        self.__balance = to_money(opening_balance, allow_zero=True)
        self.__transactions: list[Transaction] = []

    @property
    def balance(self) -> Decimal:
        """Return the current balance."""
        return self.__balance

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        """Return an immutable snapshot of transaction history."""
        return tuple(self.__transactions)

    def get_balance(self) -> Decimal:
        """Return the current balance."""
        return self.__balance

    def _restore_persisted_balance(self, balance: Decimal) -> None:
        """Restore a stored balance, including a permitted current overdraft."""
        if not isinstance(balance, Decimal) or not balance.is_finite():
            raise AccountError("A finite Decimal balance is required.")
        if balance != balance.quantize(Decimal("0.01")):
            raise AccountError("Persisted balances cannot exceed two decimal places.")
        self.__balance = balance

    def _restore_persisted_transactions(self, transactions: tuple[Transaction, ...]) -> None:
        """Restore transaction history loaded from persistent storage."""
        if not all(isinstance(item, Transaction) for item in transactions):
            raise AccountError("Persisted transaction history is invalid.")
        self.__transactions = list(transactions)

    def deposit(self, amount: Decimal) -> Transaction:
        """Deposit a positive amount and record the successful operation."""
        amount = to_money(amount)
        transaction = Transaction(
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            description=f"Deposit into {self.account_number}",
        )

        self.__balance += amount
        self.__transactions.append(transaction)
        return transaction

    @abstractmethod
    def withdraw(self, amount: Decimal) -> Transaction:
        """Withdraw money according to the concrete account's policy."""
        raise NotImplementedError

    def _validate_withdrawal(
        self,
        amount: Decimal,
        minimum_balance: Decimal,
    ) -> Decimal:
        """Validate a withdrawal against a permitted minimum balance.

        A negative minimum represents an allowed overdraft. The validated
        amount is returned so callers can safely reuse the normalized value.
        """
        amount = to_money(amount)
        minimum_balance = Decimal(str(minimum_balance)).quantize(
            Decimal("0.01")
        )

        if not minimum_balance.is_finite():
            raise AccountError("Invalid account withdrawal limit.")

        if self.__balance - amount < minimum_balance:
            if minimum_balance > 0:
                raise MinimumBalanceError(
                    "Withdrawal would violate the minimum balance."
                )
            raise InsufficientFundsError(
                "Insufficient account balance."
            )

        return amount

    def _complete_withdrawal(
        self,
        amount: Decimal,
        minimum_balance: Decimal,
    ) -> Transaction:
        """Validate and complete a normal withdrawal."""
        amount = self._validate_withdrawal(amount, minimum_balance)
        transaction = Transaction(
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            description=f"Withdrawal from {self.account_number}",
        )

        self.__balance -= amount
        self.__transactions.append(transaction)
        return transaction

    def _validate_transfer_out(self, amount: Decimal) -> Decimal:
        """Validate an outgoing transfer against the account's base policy.

        Savings and current accounts override this method to apply their
        configured minimum-balance or overdraft rule.
        """
        return self._validate_withdrawal(amount, Decimal("0.00"))

    def _apply_transfer(self, transaction: Transaction) -> None:
        """Apply one already-validated transfer entry to this account.

        This is an internal service helper. It accepts only transfer
        transaction types and derives the balance direction from the type.
        """
        if not isinstance(transaction, Transaction):
            raise AccountError("A valid transfer transaction is required.")

        amount = to_money(transaction.amount)

        if transaction.transaction_type == TransactionType.TRANSFER_OUT:
            self.__balance -= amount
        elif transaction.transaction_type == TransactionType.TRANSFER_IN:
            self.__balance += amount
        else:
            raise AccountError("Invalid transaction type for a transfer.")

        self.__transactions.append(transaction)

    def _snapshot_transfer_state(self) -> tuple[Decimal, int]:
        """Capture the balance and history length for transfer rollback."""
        return self.__balance, len(self.__transactions)

    def _restore_transfer_state(
        self,
        snapshot: tuple[Decimal, int],
    ) -> None:
        """Restore a previous transfer snapshot after an operation fails.

        Only transactions appended after the snapshot are removed. Existing
        account history is left untouched.
        """
        previous_balance, previous_history_length = snapshot
        self.__balance = previous_balance
        del self.__transactions[previous_history_length:]

    def _get_account_summary(self) -> dict[str, Any]:
        """Return basic account information for presentation code."""
        return {
            "owner": self.owner.full_name,
            "account_number": self.account_number,
            "account_type": self.__class__.__name__,
            "balance": self.__balance,
        }
