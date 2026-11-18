"""Savings account implementation and minimum-balance policy."""

from decimal import Decimal

from exceptions import ValidationError
from models.account import BankAccount
from models.customer import Customer
from models.transaction import Transaction
from utils.validators import to_money


class SavingsAccount(BankAccount):
    """Bank account that requires a configurable minimum balance.

    The minimum balance is checked when the account is opened and whenever a
    withdrawal is attempted. A withdrawal that would take the balance below
    the configured floor is rejected.
    """

    def __init__(
        self,
        owner: Customer,
        account_number: str,
        opening_balance: Decimal = Decimal("0.00"),
        minimum_balance: Decimal = Decimal("1000.00"),
    ) -> None:
        """Initialize a savings account with its minimum-balance rule.

        Args:
            owner: Customer who owns the account.
            account_number: Unique account number.
            opening_balance: Initial account balance.
            minimum_balance: Lowest permitted balance after a withdrawal.
                Zero disables the minimum-balance restriction.

        Raises:
            ValidationError: If the opening balance is below the required
                minimum balance.
        """
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

        super().__init__(
            owner,
            account_number,
            opening_balance,
        )

    def withdraw(self, amount: Decimal) -> Transaction:
        """Withdraw money while preserving the minimum balance."""
        return self._complete_withdrawal(
            amount,
            self.minimum_balance,
        )
