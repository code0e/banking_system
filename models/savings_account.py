"""Savings account implementation and minimum-balance policy."""

from decimal import Decimal

from exceptions import ValidationError
from models.account import BankAccount
from models.customer import Customer
from models.transaction import Transaction
from utils.validators import to_money


class SavingsAccount(BankAccount):
    """Account that must retain its configured minimum balance."""

    def __init__(
        self,
        owner: Customer,
        account_number: str,
        opening_balance: Decimal = Decimal("0.00"),
        minimum_balance: Decimal = Decimal("1000.00"),
    ) -> None:
        """Initialize the savings account and validate its opening balance."""
        self.minimum_balance = to_money(
            minimum_balance, allow_zero=True
        )
        opening_balance = to_money(
            opening_balance, allow_zero=True
        )

        if opening_balance < self.minimum_balance:
            raise ValidationError(
                "Opening balance must meet the minimum balance requirement."
            )

        super().__init__(owner, account_number, opening_balance)

    def withdraw(self, amount: Decimal) -> Transaction:
        """Withdraw while preserving the configured minimum balance."""
        return self._complete_withdrawal(
            amount,
            self.minimum_balance,
        )

    def _validate_transfer_out(self, amount: Decimal) -> Decimal:
        """Prevent outgoing transfers from breaching the savings minimum."""
        return self._validate_withdrawal(
            amount,
            self.minimum_balance,
        )
