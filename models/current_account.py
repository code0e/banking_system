"""Current account implementation and optional overdraft policy."""

from decimal import Decimal

from models.account import BankAccount
from models.customer import Customer
from models.transaction import Transaction
from utils.validators import to_money


class CurrentAccount(BankAccount):
    """Current account that can optionally support an overdraft.

    The overdraft limit defaults to zero, meaning withdrawals cannot exceed
    the available balance. When a positive limit is configured, the balance
    may become negative, but never lower than the negative overdraft limit.
    """

    def __init__(
        self,
        owner: Customer,
        account_number: str,
        opening_balance: Decimal = Decimal("0.00"),
        overdraft_limit: Decimal = Decimal("0.00"),
    ) -> None:
        """Initialize a current account.

        Args:
            owner: Customer who owns the account.
            account_number: Unique account number.
            opening_balance: Initial account balance.
            overdraft_limit: Maximum permitted amount below zero. The
                default of zero disables overdraft use.
        """
        self.overdraft_limit = to_money(
            overdraft_limit, allow_zero=True
        )

        super().__init__(
            owner,
            account_number,
            opening_balance,
        )

    def withdraw(self, amount: Decimal) -> Transaction:
        """Withdraw money without exceeding the configured overdraft limit."""
        allowed_minimum = -self.overdraft_limit

        return self._complete_withdrawal(
            amount,
            allowed_minimum,
        )
