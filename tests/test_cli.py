"""Tests for the interactive Banking Management System CLI."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cli.app import BankingCLI
from database import Database
from services.auth_service import AuthService
from services.bank_service import BankService


class BankingCLITests(unittest.TestCase):
    """Exercise complete CLI journeys with injected terminal functions."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "cli_test.db")
        self.bank = BankService(self.database)
        self.auth = AuthService(self.database, bank_service=self.bank)
        self.outputs: list[str] = []

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def build_cli(self, inputs: list[str], passwords: list[str]) -> BankingCLI:
        input_values = iter(inputs)
        password_values = iter(passwords)
        return BankingCLI(
            self.auth,
            input_fn=lambda _prompt: next(input_values),
            output_fn=self.outputs.append,
            password_fn=lambda _prompt: next(password_values),
        )

    def test_registration_login_account_creation_and_logout(self) -> None:
        cli = self.build_cli(
            [
                "1", "Ada Lovelace", "ada@example.com", "08012345678",
                "2", "ada@example.com", "3", "0", "0",
                "1", "0", "0",
            ],
            ["SecurePass123!", "SecurePass123!", "SecurePass123!"],
        )
        cli.run()

        self.assertTrue(any("Registration successful" in line for line in self.outputs))
        self.assertTrue(any("Login successful" in line for line in self.outputs))
        self.assertTrue(any("Current account created" in line for line in self.outputs))
        self.assertTrue(any("You have been logged out" in line for line in self.outputs))
        customer = self.bank.get_customer_by_email("ada@example.com")
        accounts = self.bank.get_customer_accounts(customer.customer_id)
        self.assertEqual(len(accounts), 1)
        self.assertEqual(type(accounts[0]).__name__, "CurrentAccount")

    def test_password_mismatch_does_not_register_customer(self) -> None:
        cli = self.build_cli(
            ["1", "Grace Hopper", "grace@example.com", "", "0"],
            ["SecurePass123!", "DifferentPass123!"],
        )
        cli.run()

        self.assertTrue(any("passwords do not match" in line for line in self.outputs))
        self.assertEqual(self.bank.get_total_customers(), 0)

    def test_invalid_welcome_choice_is_handled(self) -> None:
        cli = self.build_cli(["invalid", "0"], [])
        cli.run()
        self.assertTrue(any("Invalid option" in line for line in self.outputs))


if __name__ == "__main__":
    unittest.main()
