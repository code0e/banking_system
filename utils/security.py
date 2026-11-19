"""Password policy and password hashing utilities.

PBKDF2-HMAC-SHA256 is provided by Python's standard library. A fresh random
salt is generated for every password, and comparisons use constant-time
``hmac.compare_digest``.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import string

from exceptions import WeakPasswordError


class PasswordHasher:
    """Hash and verify passwords using salted PBKDF2-HMAC-SHA256."""

    ALGORITHM = "pbkdf2_sha256"
    ITERATIONS = 310_000
    SALT_BYTES = 16
    HASH_BYTES = 32
    MIN_LENGTH = 10
    MAX_LENGTH = 128

    @classmethod
    def validate_password(cls, password: str) -> None:
        """Enforce a minimum length and character diversity policy."""
        if not isinstance(password, str):
            raise WeakPasswordError("Password must be text.")
        if len(password) > cls.MAX_LENGTH:
            raise WeakPasswordError(
                f"Password cannot exceed {cls.MAX_LENGTH} characters."
            )
        if len(password) < cls.MIN_LENGTH:
            raise WeakPasswordError(
                f"Password must contain at least {cls.MIN_LENGTH} characters."
            )
        if not any(char.islower() for char in password):
            raise WeakPasswordError("Password must contain a lowercase letter.")
        if not any(char.isupper() for char in password):
            raise WeakPasswordError("Password must contain an uppercase letter.")
        if not any(char.isdigit() for char in password):
            raise WeakPasswordError("Password must contain a number.")
        if not any(char in string.punctuation for char in password):
            raise WeakPasswordError("Password must contain a special character.")

    @classmethod
    def hash_password(cls, password: str) -> tuple[str, str, int]:
        """Return ``(salt_hex, digest_hex, iterations)`` for a password."""
        cls.validate_password(password)
        salt = secrets.token_bytes(cls.SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, cls.ITERATIONS,
            dklen=cls.HASH_BYTES,
        )
        return salt.hex(), digest.hex(), cls.ITERATIONS

    @staticmethod
    def verify_password(
        password: str,
        salt_hex: str,
        expected_hash_hex: str,
        iterations: int,
    ) -> bool:
        """Verify a password against stored salt, digest, and work factor."""
        if not isinstance(password, str):
            return False
        try:
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(expected_hash_hex)
            if len(salt) != PasswordHasher.SALT_BYTES:
                return False
            if len(expected) != PasswordHasher.HASH_BYTES:
                return False
            if not isinstance(iterations, int) or iterations < 100_000:
                return False
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, iterations,
                dklen=len(expected),
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError, OverflowError):
            return False
