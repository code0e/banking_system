"""Current account implementation and optional overdraft policy."""

from decimal import Decimal

from models.account import BankAccount
from models.customer import Customer
from models.transaction import Transaction
from utils.validators import to_money


class CurrentAccount(BankAccount):
    """Current account with an optional overdraft facility."""

    def __init__(
        self,
        owner: Customer,
        account_number: str,
        opening_balance: Decimal = Decimal("0.00"),
        overdraft_limit: Decimal = Decimal("0.00"),
    ) -> None:
        """Initialize a current account with its overdraft limit."""
        self.overdraft_limit = to_money(
            overdraft_limit, allow_zero=True
        )
        super().__init__(owner, account_number, opening_balance)

    def withdraw(self, amount: Decimal) -> Transaction:
        """Withdraw without exceeding the configured overdraft limit."""
        return self._complete_withdrawal(
            amount,
            -self.overdraft_limit,
        )

    def _validate_transfer_out(self, amount: Decimal) -> Decimal:
        """Validate an outgoing transfer using the overdraft allowance."""
        return self._validate_withdrawal(
            amount,
            -self.overdraft_limit,
        )
