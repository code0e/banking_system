"""Integration tests for SQLite-backed banking operations."""
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from database import Database
from services.bank_service import BankService


class PersistenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / 'test_bank.db')
        self.bank = BankService(self.database)
        self.customer = self.bank.register_customer('Ada Lovelace', 'ada@example.com')
        self.savings = self.bank.create_savings_account(self.customer.customer_id, Decimal('5000.00'), Decimal('1000.00'))
        self.current = self.bank.create_current_account(self.customer.customer_id, Decimal('2000.00'))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_customers_and_accounts_survive_service_restart(self):
        restarted = BankService(Database(self.database.path))
        self.assertEqual(restarted.get_customer(self.customer.customer_id).email, 'ada@example.com')
        self.assertEqual(restarted.get_account(self.savings.account_number).balance, Decimal('5000.00'))
        self.assertEqual(restarted.get_account(self.current.account_number).balance, Decimal('2000.00'))

    def test_deposit_and_withdrawal_persist_balance_and_history(self):
        self.bank.deposit(self.savings.account_number, Decimal('500.00'))
        self.bank.withdraw(self.savings.account_number, Decimal('250.00'))
        restarted = BankService(Database(self.database.path))
        account = restarted.get_account(self.savings.account_number)
        self.assertEqual(account.balance, Decimal('5250.00'))
        self.assertEqual(len(account.transactions), 2)

    def test_transfer_persists_both_sides(self):
        self.bank.transfer(self.current.account_number, self.savings.account_number, Decimal('300.00'))
        restarted = BankService(Database(self.database.path))
        sender = restarted.get_account(self.current.account_number)
        recipient = restarted.get_account(self.savings.account_number)
        self.assertEqual(sender.balance, Decimal('1700.00'))
        self.assertEqual(recipient.balance, Decimal('5300.00'))
        self.assertEqual(len(sender.transactions), 1)
        self.assertEqual(len(recipient.transactions), 1)
        self.assertEqual(sender.transactions[0].reference, recipient.transactions[0].reference)

    def test_current_account_overdraft_survives_restart(self):
        current = self.bank.create_current_account(self.customer.customer_id, Decimal('100.00'), Decimal('500.00'))
        self.bank.withdraw(current.account_number, Decimal('250.00'))
        restarted = BankService(Database(self.database.path))
        restored = restarted.get_account(current.account_number)
        self.assertEqual(restored.balance, Decimal('-150.00'))

    def test_failed_withdrawal_does_not_persist_or_change_balance(self):
        before = self.savings.balance
        with self.assertRaises(Exception):
            self.bank.withdraw(self.savings.account_number, Decimal('10000.00'))
        restarted = BankService(Database(self.database.path))
        restored = restarted.get_account(self.savings.account_number)
        self.assertEqual(restored.balance, before)
        self.assertEqual(restored.transactions, ())


if __name__ == '__main__':
    unittest.main()
