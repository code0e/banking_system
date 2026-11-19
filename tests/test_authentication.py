"""Integration tests for customer authentication and session security."""
import tempfile
import time
import unittest
from decimal import Decimal
from datetime import timedelta
from pathlib import Path

from database import Database
from exceptions import (
    AccountOwnershipError,
    CustomerAlreadyExistsError,
    InvalidCredentialsError,
    SessionNotFoundError,
    WeakPasswordError,
)
from services.auth_service import AuthService
from utils.security import PasswordHasher


class PasswordHasherTests(unittest.TestCase):
    def test_hash_is_not_plaintext_and_can_be_verified(self):
        salt, digest, iterations = PasswordHasher.hash_password("SecurePass123!")
        self.assertNotEqual(digest, "SecurePass123!")
        self.assertTrue(PasswordHasher.verify_password("SecurePass123!", salt, digest, iterations))

    def test_each_hash_uses_a_unique_salt(self):
        first = PasswordHasher.hash_password("SecurePass123!")
        second = PasswordHasher.hash_password("SecurePass123!")
        self.assertNotEqual(first[0], second[0])
        self.assertNotEqual(first[1], second[1])

    def test_wrong_password_fails_verification(self):
        salt, digest, iterations = PasswordHasher.hash_password("SecurePass123!")
        self.assertFalse(PasswordHasher.verify_password("WrongPass123!", salt, digest, iterations))

    def test_weak_password_is_rejected(self):
        with self.assertRaises(WeakPasswordError):
            PasswordHasher.hash_password("weak")

    def test_password_longer_than_policy_limit_is_rejected(self):
        with self.assertRaises(WeakPasswordError):
            PasswordHasher.hash_password("A1!a" + "x" * 130)

    def test_malformed_hash_data_fails_safely(self):
        self.assertFalse(PasswordHasher.verify_password("anything", "bad", "bad", 310000))


class AuthenticationServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp.name) / "auth.db")
        self.auth = AuthService(self.database)
        self.password = "SecurePass123!"
        self.customer = self.auth.register(
            "Ada Lovelace", "ada@example.com", self.password, "08012345678"
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_registration_persists_customer_and_credential(self):
        with self.database.connect() as connection:
            profile = connection.execute(
                "SELECT * FROM customers WHERE customer_id = ?",
                (self.customer.customer_id,),
            ).fetchone()
            credential = connection.execute(
                "SELECT * FROM customer_credentials WHERE customer_id = ?",
                (self.customer.customer_id,),
            ).fetchone()
        self.assertIsNotNone(profile)
        self.assertIsNotNone(credential)
        self.assertNotIn(self.password, tuple(credential))

    def test_legacy_customer_can_be_enrolled_by_trusted_migration_flow(self):
        from services.bank_service import BankService
        legacy = BankService(self.database).register_customer(
            "Legacy User", "legacy@example.com"
        )
        self.auth.enroll_existing_customer(legacy.customer_id, self.password)
        session = self.auth.login("legacy@example.com", self.password)
        self.assertEqual(session.customer.customer_id, legacy.customer_id)

    def test_duplicate_email_is_rejected_case_insensitively(self):
        with self.assertRaises(CustomerAlreadyExistsError):
            self.auth.register("Another Ada", "ADA@example.com", self.password)

    def test_weak_password_does_not_create_customer(self):
        with self.assertRaises(WeakPasswordError):
            self.auth.register("Grace Hopper", "grace@example.com", "weak")
        self.assertIsNone(self.auth.user_repository.get_credentials_by_email("grace@example.com"))

    def test_login_returns_session(self):
        session = self.auth.login("ADA@example.com", self.password)
        self.assertEqual(session.customer.customer_id, self.customer.customer_id)
        self.assertTrue(session.token)

    def test_wrong_password_is_rejected(self):
        with self.assertRaises(InvalidCredentialsError):
            self.auth.login("ada@example.com", "WrongPass123!")

    def test_unknown_email_is_rejected(self):
        with self.assertRaises(InvalidCredentialsError):
            self.auth.login("unknown@example.com", self.password)

    def test_session_authenticates_customer(self):
        session = self.auth.login("ada@example.com", self.password)
        customer = self.auth.require_customer(session.token)
        self.assertEqual(customer.customer_id, self.customer.customer_id)

    def test_logout_invalidates_session(self):
        session = self.auth.login("ada@example.com", self.password)
        self.auth.logout(session.token)
        with self.assertRaises(SessionNotFoundError):
            self.auth.require_customer(session.token)

    def test_unknown_session_is_rejected(self):
        with self.assertRaises(SessionNotFoundError):
            self.auth.require_customer("not-a-real-token")

    def test_expired_session_is_rejected(self):
        short_auth = AuthService(self.database, session_lifetime=timedelta(milliseconds=1))
        session = short_auth.login("ada@example.com", self.password)
        time.sleep(0.01)
        with self.assertRaises(SessionNotFoundError):
            short_auth.require_customer(session.token)

    def test_password_change_revokes_sessions_and_updates_credentials(self):
        session = self.auth.login("ada@example.com", self.password)
        self.auth.change_password(session.token, self.password, "NewSecurePass456!")
        with self.assertRaises(SessionNotFoundError):
            self.auth.require_customer(session.token)
        with self.assertRaises(InvalidCredentialsError):
            self.auth.login("ada@example.com", self.password)
        new_session = self.auth.login("ada@example.com", "NewSecurePass456!")
        self.assertEqual(new_session.customer.customer_id, self.customer.customer_id)

    def test_password_change_requires_current_password(self):
        session = self.auth.login("ada@example.com", self.password)
        with self.assertRaises(InvalidCredentialsError):
            self.auth.change_password(session.token, "WrongPass123!", "NewSecurePass456!")

    def test_authenticated_customer_is_available_to_bank_service(self):
        session = self.auth.login("ada@example.com", self.password)
        account = self.auth.bank_service.create_current_account(session.customer.customer_id)
        self.assertEqual(account.owner.customer_id, self.customer.customer_id)

    def test_sessions_are_invalidated_when_service_restarts(self):
        session = self.auth.login("ada@example.com", self.password)
        restarted = AuthService(self.database)
        with self.assertRaises(SessionNotFoundError):
            restarted.require_customer(session.token)

    def test_authenticated_operations_require_a_session(self):
        account = self.auth.bank_service.create_current_account(
            self.customer.customer_id, opening_balance=Decimal("500.00")
        )
        session = self.auth.login("ada@example.com", self.password)
        transaction = self.auth.deposit(
            session.token, account.account_number, Decimal("50.00")
        )
        self.assertEqual(transaction.amount, Decimal("50.00"))
        self.assertEqual(
            self.auth.get_account(session.token, account.account_number).balance,
            Decimal("550.00"),
        )

    def test_session_cannot_access_another_customers_account(self):
        other = self.auth.register("Grace Hopper", "grace@example.com", self.password)
        other_account = self.auth.bank_service.create_current_account(
            other.customer_id, opening_balance=Decimal("500.00")
        )
        session = self.auth.login("ada@example.com", self.password)
        with self.assertRaises(AccountOwnershipError):
            self.auth.get_account(session.token, other_account.account_number)
        with self.assertRaises(AccountOwnershipError):
            self.auth.deposit(session.token, other_account.account_number, Decimal("10.00"))

    def test_unauthenticated_deposit_is_rejected(self):
        account = self.auth.bank_service.create_current_account(
            self.customer.customer_id, opening_balance=Decimal("500.00")
        )
        with self.assertRaises(SessionNotFoundError):
            self.auth.deposit("invalid-session", account.account_number, Decimal("10.00"))

    def test_active_session_count(self):
        self.assertEqual(self.auth.active_session_count(), 0)
        self.auth.login("ada@example.com", self.password)
        self.assertEqual(self.auth.active_session_count(), 1)


if __name__ == "__main__":
    unittest.main()
