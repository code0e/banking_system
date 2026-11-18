
import unittest
from decimal import Decimal

from exceptions import (
    AccountNotFoundError,
    AccountOwnershipError,
    CustomerAlreadyExistsError,
    CustomerNotFoundError,
    ValidationError,
)
from models.savings_account import SavingsAccount
from models.current_account import CurrentAccount
from services.bank_service import BankService


class TestBankService(unittest.TestCase):

    def setUp(self):
        self.bank = BankService()

        self.customer = self.bank.register_customer(
            full_name="Logic",
            email="logic@example.com",
            phone="08012345678",
        )

    def test_customer_registration(self):
        self.assertEqual(
            self.customer.full_name,
            "Logic",
        )

        self.assertEqual(
            self.bank.get_total_customers(),
            1,
        )

    def test_customer_email_is_case_insensitive(self):
        customer = self.bank.get_customer_by_email(
            "LOGIC@EXAMPLE.COM"
        )

        self.assertEqual(
            customer.customer_id,
            self.customer.customer_id,
        )

    def test_duplicate_customer_email(self):
        with self.assertRaises(CustomerAlreadyExistsError):
            self.bank.register_customer(
                "Another Logic",
                "LOGIC@EXAMPLE.COM",
            )

    def test_customer_not_found(self):
        with self.assertRaises(CustomerNotFoundError):
            self.bank.get_customer("unknown-id")

    def test_invalid_customer_registration(self):
        with self.assertRaises(ValidationError):
            self.bank.register_customer(
                "",
                "invalid@example.com",
            )

    def test_savings_account_creation(self):
        account = self.bank.create_savings_account(
            self.customer.customer_id,
            Decimal("5000"),
        )

        self.assertIsInstance(
            account,
            SavingsAccount,
        )

        self.assertEqual(
            account.owner.customer_id,
            self.customer.customer_id,
        )

    def test_current_account_creation(self):
        account = self.bank.create_current_account(
            self.customer.customer_id,
            Decimal("5000"),
        )

        self.assertIsInstance(
            account,
            CurrentAccount,
        )

    def test_account_numbers_are_unique(self):
        account_one = self.bank.create_current_account(
            self.customer.customer_id,
        )

        account_two = self.bank.create_current_account(
            self.customer.customer_id,
        )

        self.assertNotEqual(
            account_one.account_number,
            account_two.account_number,
        )

    def test_account_number_has_ten_digits(self):
        account = self.bank.create_current_account(
            self.customer.customer_id,
        )

        self.assertEqual(
            len(account.account_number),
            10,
        )

        self.assertTrue(
            account.account_number.isdigit()
        )

    def test_multiple_accounts_per_customer(self):
        self.bank.create_savings_account(
            self.customer.customer_id,
            Decimal("5000"),
        )

        self.bank.create_current_account(
            self.customer.customer_id,
            Decimal("2000"),
        )

        accounts = self.bank.get_customer_accounts(
            self.customer.customer_id
        )

        self.assertEqual(len(accounts), 2)

    def test_account_lookup(self):
        account = self.bank.create_current_account(
            self.customer.customer_id,
        )

        retrieved = self.bank.get_account(
            account.account_number
        )

        self.assertEqual(
            retrieved.account_number,
            account.account_number,
        )

    def test_account_not_found(self):
        with self.assertRaises(AccountNotFoundError):
            self.bank.get_account("0000000000")

    def test_account_ownership_validation(self):
        account = self.bank.create_current_account(
            self.customer.customer_id,
        )

        another_customer = self.bank.register_customer(
            "Judith",
            "judith@example.com",
        )

        with self.assertRaises(AccountOwnershipError):
            self.bank.get_account(
                account.account_number,
                another_customer.customer_id,
            )

    def test_account_owner_can_access_account(self):
        account = self.bank.create_current_account(
            self.customer.customer_id,
        )

        retrieved = self.bank.get_account(
            account.account_number,
            self.customer.customer_id,
        )

        self.assertIs(retrieved, account)

    def test_customer_account_count(self):
        self.bank.create_current_account(
            self.customer.customer_id,
        )

        self.bank.create_savings_account(
            self.customer.customer_id,
            Decimal("5000"),
        )

        self.assertEqual(
            self.bank.get_total_customer_accounts(
                self.customer.customer_id
            ),
            2,
        )

    def test_bank_totals(self):
        self.bank.create_current_account(
            self.customer.customer_id,
        )

        self.assertEqual(
            self.bank.get_total_customers(),
            1,
        )

        self.assertEqual(
            self.bank.get_total_accounts(),
            1,
        )

    def test_accounts_are_isolated_between_customers(self):
        another_customer = self.bank.register_customer(
            "Judith",
            "judith@example.com",
        )

        self.bank.create_current_account(
            self.customer.customer_id,
        )

        self.bank.create_savings_account(
            another_customer.customer_id,
            Decimal("5000"),
        )

        self.assertEqual(
            len(
                self.bank.get_customer_accounts(
                    self.customer.customer_id
                )
            ),
            1,
        )

        self.assertEqual(
            len(
                self.bank.get_customer_accounts(
                    another_customer.customer_id
                )
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
