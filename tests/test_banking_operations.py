
import unittest
from decimal import Decimal

from exceptions import (
    AccountNotFoundError,
    AccountOwnershipError,
    InsufficientFundsError,
    InvalidAmountError,
    MinimumBalanceError,
)
from services.bank_service import BankService


class TestBankingOperations(unittest.TestCase):

    def setUp(self):
        self.bank = BankService()

        self.customer = self.bank.register_customer(
            full_name="Logic Tester",
            email="logic@example.com",
            phone="08012345678",
        )

        self.savings = self.bank.create_savings_account(
            customer_id=self.customer.customer_id,
            opening_balance=Decimal("5000.00"),
            minimum_balance=Decimal("1000.00"),
        )

        self.current = self.bank.create_current_account(
            customer_id=self.customer.customer_id,
            opening_balance=Decimal("0.00"),
        )

    def test_successful_deposit(self):
        transaction = self.bank.deposit(
            self.savings.account_number,
            Decimal("2000.00"),
            self.customer.customer_id,
        )

        self.assertEqual(
            self.savings.balance,
            Decimal("7000.00"),
        )

        self.assertEqual(
            transaction.amount,
            Decimal("2000.00"),
        )

    def test_successful_withdrawal(self):
        transaction = self.bank.withdraw(
            self.savings.account_number,
            Decimal("1000.00"),
            self.customer.customer_id,
        )

        self.assertEqual(
            self.savings.balance,
            Decimal("4000.00"),
        )

        self.assertEqual(
            transaction.amount,
            Decimal("1000.00"),
        )

    def test_savings_minimum_balance_is_enforced(self):
        with self.assertRaises(MinimumBalanceError):
            self.bank.withdraw(
                self.savings.account_number,
                Decimal("4500.00"),
                self.customer.customer_id,
            )

        self.assertEqual(
            self.savings.balance,
            Decimal("5000.00"),
        )

    def test_current_account_insufficient_funds(self):
        with self.assertRaises(InsufficientFundsError):
            self.bank.withdraw(
                self.current.account_number,
                Decimal("500.00"),
                self.customer.customer_id,
            )

        self.assertEqual(
            self.current.balance,
            Decimal("0.00"),
        )

    def test_invalid_deposit_does_not_change_balance(self):
        with self.assertRaises(InvalidAmountError):
            self.bank.deposit(
                self.savings.account_number,
                Decimal("-100.00"),
                self.customer.customer_id,
            )

        self.assertEqual(
            self.savings.balance,
            Decimal("5000.00"),
        )

    def test_float_deposit_is_rejected(self):
        with self.assertRaises(InvalidAmountError):
            self.bank.deposit(
                self.savings.account_number,
                100.50,
                self.customer.customer_id,
            )

    def test_account_not_found(self):
        with self.assertRaises(AccountNotFoundError):
            self.bank.deposit(
                "9999999999",
                Decimal("100.00"),
            )

    def test_customer_cannot_deposit_into_another_customers_account(self):
        another_customer = self.bank.register_customer(
            full_name="Another Customer",
            email="another@example.com",
        )

        with self.assertRaises(AccountOwnershipError):
            self.bank.deposit(
                self.savings.account_number,
                Decimal("100.00"),
                another_customer.customer_id,
            )

    def test_customer_cannot_withdraw_from_another_customers_account(self):
        another_customer = self.bank.register_customer(
            full_name="Another Customer",
            email="another@example.com",
        )

        with self.assertRaises(AccountOwnershipError):
            self.bank.withdraw(
                self.savings.account_number,
                Decimal("100.00"),
                another_customer.customer_id,
            )

    def test_transaction_history(self):
        self.bank.deposit(
            self.savings.account_number,
            Decimal("500.00"),
            self.customer.customer_id,
        )

        self.bank.withdraw(
            self.savings.account_number,
            Decimal("200.00"),
            self.customer.customer_id,
        )

        history = self.bank.get_transaction_history(
            self.savings.account_number,
            self.customer.customer_id,
        )

        self.assertEqual(len(history), 2)
        self.assertEqual(
            history[0].amount,
            Decimal("500.00"),
        )
        self.assertEqual(
            history[1].amount,
            Decimal("200.00"),
        )

    def test_transaction_references_are_unique(self):
        first = self.bank.deposit(
            self.savings.account_number,
            Decimal("100.00"),
            self.customer.customer_id,
        )

        second = self.bank.deposit(
            self.savings.account_number,
            Decimal("200.00"),
            self.customer.customer_id,
        )

        self.assertNotEqual(
            first.reference,
            second.reference,
        )

    def test_statement_contains_account_information(self):
        self.bank.deposit(
            self.savings.account_number,
            Decimal("500.00"),
            self.customer.customer_id,
        )

        statement = self.bank.generate_statement(
            self.savings.account_number,
            self.customer.customer_id,
        )

        self.assertIn("LOGICBANK", statement)
        self.assertIn(self.customer.full_name, statement)
        self.assertIn(self.savings.account_number, statement)
        self.assertIn("DEPOSIT", statement)
        self.assertIn("NGN 5,500.00", statement)

    def test_empty_statement(self):
        statement = self.bank.generate_statement(
            self.current.account_number,
            self.customer.customer_id,
        )

        self.assertIn("No transactions recorded.", statement)


if __name__ == "__main__":
    unittest.main()
