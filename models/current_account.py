
from decimal import Decimal

from models.account import BankAccount
from utils.validators import to_money


class CurrentAccount(BankAccount):
    """Current account with an optional overdraft facility."""

    def __init__(
        self,
        owner,
        account_number,
        opening_balance=Decimal("0.00"),
        overdraft_limit=Decimal("0.00"),
    ):
        self.overdraft_limit = to_money(
            overdraft_limit, allow_zero=True
        )

        super().__init__(
            owner,
            account_number,
            opening_balance,
        )

    def withdraw(self, amount):
        """Withdraw using the configured overdraft limit."""

        allowed_minimum = -self.overdraft_limit

        return self._complete_withdrawal(
            amount,
            allowed_minimum,
        )
