
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from exceptions import InvalidAmountError, ValidationError


CENT = Decimal("0.01")


def to_money(value, allow_zero=False):
    """Convert a valid monetary value into a two-decimal Decimal."""

    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidAmountError(
            "Money must be supplied as a Decimal, integer or string."
        )

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InvalidAmountError("Enter a valid monetary amount.")

    if not amount.is_finite():
        raise InvalidAmountError("Amount must be a finite number.")

    amount = amount.quantize(CENT, rounding=ROUND_HALF_UP)

    if amount < 0:
        raise InvalidAmountError("Amount cannot be negative.")

    if not allow_zero and amount == 0:
        raise InvalidAmountError("Amount must be greater than zero.")

    return amount


def validate_non_empty(value, field_name):
    """Validate a required string field."""

    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty.")

    return value.strip()
