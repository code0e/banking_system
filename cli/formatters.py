"""Presentation helpers for CLI monetary and account values."""
from decimal import Decimal


def format_ngn(amount: Decimal) -> str:
    """Format a Decimal amount as Nigerian naira."""
    return f"NGN {amount:,.2f}"


def account_type_label(account: object) -> str:
    """Return a friendly account type label."""
    name = type(account).__name__
    return name.replace("Account", " Account")
