"""Tests for account repository persistence."""
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from database import Database
from models.customer import Customer
from models.savings_account import SavingsAccount
from models.current_account import CurrentAccount
from repositories.customer_repository import CustomerRepository
from repositories.account_repository import AccountRepository
from exceptions import AccountNotFoundError


class AccountRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.temp.name) / 'test.db')
        self.db.initialize()
        self.customers = CustomerRepository(self.db)
        self.repo = AccountRepository(self.db, self.customers)
        self.owner = self.customers.save(Customer('Ada Lovelace', 'ada@example.com'))
        self.savings = SavingsAccount(self.owner, '1000000001', Decimal('5000.00'), Decimal('1000.00'))
        self.current = CurrentAccount(self.owner, '1000000002', Decimal('2000.00'), Decimal('500.00'))

    def tearDown(self):
        self.temp.cleanup()

    def test_save_savings_account(self):
        self.repo.save(self.savings)
        self.assertEqual(self.repo.get_by_number(self.savings.account_number).balance, Decimal('5000.00'))

    def test_save_current_account(self):
        self.repo.save(self.current)
        restored = self.repo.get_by_number(self.current.account_number)
        self.assertIsInstance(restored, CurrentAccount)
        self.assertEqual(restored.overdraft_limit, Decimal('500.00'))

    def test_savings_subclass_is_restored(self):
        self.repo.save(self.savings)
        self.assertIsInstance(self.repo.get_by_number(self.savings.account_number), SavingsAccount)

    def test_missing_account_returns_none(self):
        self.assertIsNone(self.repo.get_by_number('missing'))

    def test_duplicate_account_number_is_rejected(self):
        self.repo.save(self.savings)
        with self.assertRaises(Exception):
            self.repo.save(SavingsAccount(self.owner, self.savings.account_number, Decimal('2000.00'), Decimal('1000.00')))

    def test_list_by_customer(self):
        self.repo.save(self.savings)
        self.repo.save(self.current)
        self.assertEqual(len(self.repo.list_by_customer(self.owner.customer_id)), 2)

    def test_list_all(self):
        self.repo.save(self.savings)
        self.repo.save(self.current)
        self.assertEqual(len(self.repo.list_all()), 2)

    def test_update_balance(self):
        self.repo.save(self.current)
        self.repo.update_balance(self.current.account_number, Decimal('3500.25'))
        self.assertEqual(self.repo.get_by_number(self.current.account_number).balance, Decimal('3500.25'))

    def test_missing_account_update_raises(self):
        with self.assertRaises(AccountNotFoundError):
            self.repo.update_balance('missing', Decimal('1.00'))

    def test_count_by_customer(self):
        self.repo.save(self.savings)
        self.repo.save(self.current)
        self.assertEqual(self.repo.count_by_customer(self.owner.customer_id), 2)

    def test_negative_current_balance_survives_reload(self):
        self.repo.save(self.current)
        self.repo.update_balance(self.current.account_number, Decimal('-150.00'))
        restored = self.repo.get_by_number(self.current.account_number)
        self.assertEqual(restored.balance, Decimal('-150.00'))

    def test_exists(self):
        self.repo.save(self.savings)
        self.assertTrue(self.repo.exists(self.savings.account_number))
        self.assertFalse(self.repo.exists('missing'))

    def test_exact_kobo_precision(self):
        account = CurrentAccount(self.owner, '1000000003', Decimal('12.34'))
        self.repo.save(account)
        self.assertEqual(self.repo.get_by_number(account.account_number).balance, Decimal('12.34'))


if __name__ == '__main__':
    unittest.main()
