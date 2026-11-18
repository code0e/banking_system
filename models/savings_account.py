
from decimal import Decimal

from exceptions import ValidationError
from models.account import BankAccount
from utils.validators import to_money


class SavingsAccount(BankAccount):
    """Bank account with a configurable minimum balance."""

    def __init__(
        self,
        owner,
        account_number,
        opening_balance=Decimal("0.00"),
        minimum_balance=Decimal("1000.00"),
    ):
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

    def withdraw(self, amount):
        """Withdraw while maintaining the minimum balance."""

        return self._complete_withdrawal(
            amount,
            self.minimum_balance,
        )
