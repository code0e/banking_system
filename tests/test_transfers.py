"""Automated tests for LogicBank's account-to-account transfers."""

import unittest
from decimal import Decimal
from unittest.mock import patch

from exceptions import (
    AccountNotFoundError,
    AccountOwnershipError,
    InsufficientFundsError,
    InvalidAmountError,
    MinimumBalanceError,
    ValidationError,
)
from models.transaction import TransactionType
from services.bank_service import BankService


class TestMoneyTransfers(unittest.TestCase):
    """Verify transfer validation, accounting, history, and rollback."""

    def setUp(self):
        """Create two customers and funded accounts for each test."""
        self.bank = BankService()
        self.sender_customer = self.bank.register_customer(
            "Logic Sender",
            "sender@example.com",
        )
        self.recipient_customer = self.bank.register_customer(
            "Judith Recipient",
            "recipient@example.com",
        )

        self.sender_savings = self.bank.create_savings_account(
            customer_id=self.sender_customer.customer_id,
            opening_balance=Decimal("10000.00"),
            minimum_balance=Decimal("1000.00"),
        )
        self.sender_current = self.bank.create_current_account(
            customer_id=self.sender_customer.customer_id,
            opening_balance=Decimal("5000.00"),
        )
        self.recipient_current = self.bank.create_current_account(
            customer_id=self.recipient_customer.customer_id,
            opening_balance=Decimal("2000.00"),
        )

    def test_successful_transfer_between_different_customers(self):
        """A successful transfer debits and credits the correct accounts."""
        outgoing, incoming = self.bank.transfer(
            self.sender_savings.account_number,
            self.recipient_current.account_number,
            Decimal("2500.00"),
            self.sender_customer.customer_id,
        )

        self.assertEqual(
            self.sender_savings.balance,
            Decimal("7500.00"),
        )
        self.assertEqual(
            self.recipient_current.balance,
            Decimal("4500.00"),
        )
        self.assertEqual(
            outgoing.transaction_type,
            TransactionType.TRANSFER_OUT,
        )
        self.assertEqual(
            incoming.transaction_type,
            TransactionType.TRANSFER_IN,
        )
        self.assertEqual(outgoing.amount, incoming.amount)
        self.assertEqual(outgoing.reference, incoming.reference)

    def test_customer_can_transfer_between_own_accounts(self):
        """A customer may transfer between their own savings and current."""
        self.bank.transfer(
            self.sender_savings.account_number,
            self.sender_current.account_number,
            Decimal("3000.00"),
            self.sender_customer.customer_id,
        )

        self.assertEqual(
            self.sender_savings.balance,
            Decimal("7000.00"),
        )
        self.assertEqual(
            self.sender_current.balance,
            Decimal("8000.00"),
        )

    def test_transfer_records_are_added_to_both_histories(self):
        """Each account receives its matching transfer record."""
        outgoing, incoming = self.bank.transfer(
            self.sender_savings.account_number,
            self.recipient_current.account_number,
            Decimal("1000.00"),
            self.sender_customer.customer_id,
        )

        self.assertEqual(
            self.sender_savings.transactions[-1],
            outgoing,
        )
        self.assertEqual(
            self.recipient_current.transactions[-1],
            incoming,
        )

    def test_transfer_requires_sender_ownership(self):
        """A customer cannot transfer from another customer's account."""
        with self.assertRaises(AccountOwnershipError):
            self.bank.transfer(
                self.sender_savings.account_number,
                self.recipient_current.account_number,
                Decimal("100.00"),
                self.recipient_customer.customer_id,
            )

    def test_sender_account_must_exist(self):
        """An unknown sender account is rejected."""
        with self.assertRaises(AccountNotFoundError):
            self.bank.transfer(
                "9999999999",
                self.recipient_current.account_number,
                Decimal("100.00"),
                self.sender_customer.customer_id,
            )

    def test_recipient_account_must_exist(self):
        """An unknown recipient account is rejected without a debit."""
        with self.assertRaises(AccountNotFoundError):
            self.bank.transfer(
                self.sender_savings.account_number,
                "9999999999",
                Decimal("100.00"),
                self.sender_customer.customer_id,
            )

        self.assertEqual(
            self.sender_savings.balance,
            Decimal("10000.00"),
        )

    def test_transfer_to_same_account_is_rejected(self):
        """An account cannot be both the sender and recipient."""
        with self.assertRaises(ValidationError):
            self.bank.transfer(
                self.sender_savings.account_number,
                self.sender_savings.account_number,
                Decimal("100.00"),
                self.sender_customer.customer_id,
            )

        self.assertEqual(
            self.sender_savings.balance,
            Decimal("10000.00"),
        )

    def test_savings_minimum_balance_is_enforced_for_transfer(self):
        """An outgoing transfer cannot breach a savings minimum."""
        with self.assertRaises(MinimumBalanceError):
            self.bank.transfer(
                self.sender_savings.account_number,
                self.recipient_current.account_number,
                Decimal("9500.00"),
                self.sender_customer.customer_id,
            )

        self.assertEqual(
            self.sender_savings.balance,
            Decimal("10000.00"),
        )
        self.assertEqual(
            self.recipient_current.balance,
            Decimal("2000.00"),
        )

    def test_insufficient_current_account_funds_are_rejected(self):
        """A current account without overdraft cannot overdraw by transfer."""
        with self.assertRaises(InsufficientFundsError):
            self.bank.transfer(
                self.sender_current.account_number,
                self.recipient_current.account_number,
                Decimal("6000.00"),
                self.sender_customer.customer_id,
            )

        self.assertEqual(
            self.sender_current.balance,
            Decimal("5000.00"),
        )

    def test_current_account_overdraft_can_be_used_for_transfer(self):
        """A configured overdraft is respected by outgoing transfers."""
        overdraft_account = self.bank.create_current_account(
            customer_id=self.sender_customer.customer_id,
            opening_balance=Decimal("1000.00"),
            overdraft_limit=Decimal("500.00"),
        )

        self.bank.transfer(
            overdraft_account.account_number,
            self.recipient_current.account_number,
            Decimal("1400.00"),
            self.sender_customer.customer_id,
        )

        self.assertEqual(
            overdraft_account.balance,
            Decimal("-400.00"),
        )

    def test_transfer_rejects_zero_amount(self):
        """A zero-value transfer is invalid."""
        with self.assertRaises(InvalidAmountError):
            self.bank.transfer(
                self.sender_savings.account_number,
                self.recipient_current.account_number,
                Decimal("0.00"),
                self.sender_customer.customer_id,
            )

    def test_transfer_rejects_negative_amount(self):
        """A negative transfer amount is invalid."""
        with self.assertRaises(InvalidAmountError):
            self.bank.transfer(
                self.sender_savings.account_number,
                self.recipient_current.account_number,
                Decimal("-10.00"),
                self.sender_customer.customer_id,
            )

    def test_transfer_rejects_float_amount(self):
        """Float input is rejected to protect monetary precision."""
        with self.assertRaises(InvalidAmountError):
            self.bank.transfer(
                self.sender_savings.account_number,
                self.recipient_current.account_number,
                100.50,
                self.sender_customer.customer_id,
            )

    def test_failed_credit_rolls_back_both_accounts_and_histories(self):
        """A failure after the debit restores both account snapshots."""
        original_recipient_apply = self.recipient_current._apply_transfer

        def apply_then_fail(transaction):
            original_recipient_apply(transaction)
            raise RuntimeError("Simulated recipient-side failure")

        sender_balance_before = self.sender_savings.balance
        recipient_balance_before = self.recipient_current.balance
        sender_history_before = self.sender_savings.transactions
        recipient_history_before = self.recipient_current.transactions

        with patch.object(
            self.recipient_current,
            "_apply_transfer",
            side_effect=apply_then_fail,
        ):
            with self.assertRaises(RuntimeError):
                self.bank.transfer(
                    self.sender_savings.account_number,
                    self.recipient_current.account_number,
                    Decimal("1000.00"),
                    self.sender_customer.customer_id,
                )

        self.assertEqual(
            self.sender_savings.balance,
            sender_balance_before,
        )
        self.assertEqual(
            self.recipient_current.balance,
            recipient_balance_before,
        )
        self.assertEqual(
            self.sender_savings.transactions,
            sender_history_before,
        )
        self.assertEqual(
            self.recipient_current.transactions,
            recipient_history_before,
        )


if __name__ == "__main__":
    unittest.main()
