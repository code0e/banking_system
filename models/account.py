
from abc import ABC, abstractmethod
from decimal import Decimal

from exceptions import (
    AccountError,
    InsufficientFundsError,
    MinimumBalanceError,
)
from models.customer import Customer
from models.transaction import Transaction, TransactionType
from utils.validators import to_money, validate_non_empty


class BankAccount(ABC):
    """Abstract base class for all LogicBank accounts."""

    def __init__(
        self,
        owner: Customer,
        account_number: str,
        opening_balance=Decimal("0.00"),
    ):
        if not isinstance(owner, Customer):
            raise AccountError("A valid customer is required.")

        self.owner = owner
        self.account_number = validate_non_empty(
            account_number, "Account number"
        )

        self.__balance = to_money(
            opening_balance, allow_zero=True
        )
        self.__transactions = []

    @property
    def balance(self):
        return self.__balance

    @property
    def transactions(self):
        return tuple(self.__transactions)

    def get_balance(self):
        return self.__balance

    def deposit(self, amount):
        amount = to_money(amount)

        self.__balance += amount

        transaction = Transaction(
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            description=f"Deposit into {self.account_number}",
        )

        self.__transactions.append(transaction)
        return transaction

    @abstractmethod
    def withdraw(self, amount):
        raise NotImplementedError

    def _complete_withdrawal(self, amount, minimum_balance):
        amount = to_money(amount)

        minimum_balance = Decimal(
            str(minimum_balance)
        ).quantize(Decimal("0.01"))

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

        self.__balance -= amount

        transaction = Transaction(
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            description=f"Withdrawal from {self.account_number}",
        )

        self.__transactions.append(transaction)
        return transaction

    def _get_account_summary(self):
        return {
            "owner": self.owner.full_name,
            "account_number": self.account_number,
            "account_type": self.__class__.__name__,
            "balance": self.__balance,
        }
