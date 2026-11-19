import unittest
from decimal import Decimal

from exceptions import (
    InsufficientFundsError,
    InvalidAmountError,
    MinimumBalanceError,
)
from models.account import BankAccount
from models.customer import Customer
from models.savings_account import SavingsAccount
from models.current_account import CurrentAccount
from models.transaction import TransactionType


class TestBankAccounts(unittest.TestCase):

    def setUp(self):
        self.customer = Customer(
            full_name="Logic",
            email="logic@example.com",
            phone="08012345678",
        )

    def test_customer_creation(self):
        self.assertEqual(self.customer.full_name, "Logic")
        self.assertEqual(
            self.customer.email,
            "logic@example.com",
        )

    def test_customer_email_is_normalized(self):
        customer = Customer(
            "Logic",
            "LOGIC@EXAMPLE.COM",
        )
        self.assertEqual(
            customer.email,
            "logic@example.com",
        )

    def test_account_is_abstract(self):
        with self.assertRaises(TypeError):
            BankAccount(
                self.customer,
                "100001",
                Decimal("5000"),
            )

    def test_savings_account_creation(self):
        account = SavingsAccount(
            self.customer,
            "100001",
            Decimal("5000"),
        )

        self.assertEqual(
            account.balance,
            Decimal("5000.00"),
        )

    def test_deposit(self):
        account = SavingsAccount(
            self.customer,
            "100001",
            Decimal("5000"),
        )

        transaction = account.deposit("2000")

        self.assertEqual(
            account.balance,
            Decimal("7000.00"),
        )

        self.assertEqual(
            transaction.transaction_type,
            TransactionType.DEPOSIT,
        )

    def test_withdrawal(self):
        account = SavingsAccount(
            self.customer,
            "100001",
            Decimal("5000"),
        )

        transaction = account.withdraw("1000")

        self.assertEqual(
            account.balance,
            Decimal("4000.00"),
        )

        self.assertEqual(
            transaction.transaction_type,
            TransactionType.WITHDRAWAL,
        )

    def test_minimum_balance_protection(self):
        account = SavingsAccount(
            self.customer,
            "100001",
            Decimal("5000"),
            Decimal("1000"),
        )

        with self.assertRaises(MinimumBalanceError):
            account.withdraw("4500")

        self.assertEqual(
            account.balance,
            Decimal("5000.00"),
        )

    def test_invalid_deposit(self):
        account = SavingsAccount(
            self.customer,
            "100001",
            Decimal("5000"),
        )

        with self.assertRaises(InvalidAmountError):
            account.deposit("-500")

        self.assertEqual(
            account.balance,
            Decimal("5000.00"),
        )

    def test_zero_withdrawal(self):
        account = CurrentAccount(
            self.customer,
            "100002",
            Decimal("5000"),
        )

        with self.assertRaises(InvalidAmountError):
            account.withdraw("0")

        self.assertEqual(
            account.balance,
            Decimal("5000.00"),
        )

    def test_current_account_without_overdraft(self):
        account = CurrentAccount(
            self.customer,
            "100002",
            Decimal("5000"),
        )

        with self.assertRaises(InsufficientFundsError):
            account.withdraw("6000")

        self.assertEqual(
            account.balance,
            Decimal("5000.00"),
        )

    def test_current_account_with_overdraft(self):
        account = CurrentAccount(
            self.customer,
            "100002",
            Decimal("1000"),
            Decimal("500"),
        )

        account.withdraw("1400")

        self.assertEqual(
            account.balance,
            Decimal("-400.00"),
        )

    def test_overdraft_limit_is_enforced(self):
        account = CurrentAccount(
            self.customer,
            "100002",
            Decimal("1000"),
            Decimal("500"),
        )

        with self.assertRaises(InsufficientFundsError):
            account.withdraw("1600")

        self.assertEqual(
            account.balance,
            Decimal("1000.00"),
        )

    def test_transaction_history(self):
        account = SavingsAccount(
            self.customer,
            "100001",
            Decimal("5000"),
        )

        account.deposit("1000")
        account.withdraw("500")

        self.assertEqual(len(account.transactions), 2)

    def test_transaction_history_is_read_only(self):
        account = SavingsAccount(
            self.customer,
            "100001",
            Decimal("5000"),
        )

        account.deposit("1000")

        history = account.transactions

        with self.assertRaises(AttributeError):
            history.append("invalid")

    def test_money_does_not_accept_float(self):
        account = CurrentAccount(
            self.customer,
            "100002",
            Decimal("5000"),
        )

        with self.assertRaises(InvalidAmountError):
            account.deposit(100.50)


if __name__ == "__main__":
    unittest.main()
