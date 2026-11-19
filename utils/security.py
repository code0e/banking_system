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
    MIN_ITERATIONS = 100_000
    MAX_ITERATIONS = 2_000_000
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

    @classmethod
    def verify_password(
        cls,
        password: str,
        salt_hex: str,
        expected_hash_hex: str,
        iterations: int,
    ) -> bool:
        """Verify a stored hash while bounding untrusted input and CPU cost.

        The iteration count is persisted with each credential. It must be
        bounded before PBKDF2 is called so a corrupted or tampered database
        cannot request an effectively unbounded amount of CPU work.
        """
        if not isinstance(password, str) or len(password) > cls.MAX_LENGTH:
            return False
        if not isinstance(salt_hex, str) or len(salt_hex) != cls.SALT_BYTES * 2:
            return False
        if (
            not isinstance(expected_hash_hex, str)
            or len(expected_hash_hex) != cls.HASH_BYTES * 2
        ):
            return False
        if (
            isinstance(iterations, bool)
            or not isinstance(iterations, int)
            or not cls.MIN_ITERATIONS <= iterations <= cls.MAX_ITERATIONS
        ):
            return False

        try:
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(expected_hash_hex)
            if len(salt) != cls.SALT_BYTES or len(expected) != cls.HASH_BYTES:
                return False
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                iterations,
                dklen=cls.HASH_BYTES,
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError, OverflowError):
            return False
