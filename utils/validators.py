"""
Input validation and monetary normalization utilities.

This module contains reusable validation functions used
throughout the LogicBank application.

Responsibilities:

    1. Convert valid monetary inputs into Decimal values.
    2. Enforce two-decimal-place monetary precision.
    3. Reject invalid, negative and non-finite monetary values.
    4. Validate required string fields.
    5. Provide consistent validation errors across the application.

Financial calculations should use Decimal rather than float
to avoid floating-point precision errors.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from exceptions import InvalidAmountError, ValidationError


# One Nigerian currency unit is represented to two decimal places.
# This constant is used when normalizing monetary values.
CENT = Decimal("0.01")


def to_money(value, allow_zero=False) -> Decimal:
    """
    Validate and convert an input into a two-decimal Decimal value.

    This function is the central monetary validation utility
    used by LogicBank.

    Accepted input types:
        - Decimal
        - Integer
        - Numeric string

    Rejected input types:
        - Float
        - Boolean
        - Non-numeric values

    Monetary values are rounded to two decimal places using
    the ROUND_HALF_UP rounding strategy.

    Args:
        value:
            The monetary value to validate and convert.

        allow_zero:
            Determines whether a zero monetary amount is allowed.
            Defaults to False.

    Returns:
        Decimal:
            A validated monetary amount rounded to two decimal
            places.

    Raises:
        InvalidAmountError:
            If the input is a boolean, float, invalid numeric
            value, negative amount or non-finite number.

        InvalidAmountError:
            If the amount is zero and allow_zero is False.

    Examples:
        >>> to_money("1500.50")
        Decimal('1500.50')

        >>> to_money(2500)
        Decimal('2500.00')

        >>> to_money("100.567")
        Decimal('100.57')

        >>> to_money("0", allow_zero=True)
        Decimal('0.00')
    """

    # Booleans are technically subclasses of integers in Python.
    # Floats are rejected because they can introduce precision
    # errors when used for financial calculations.
    if isinstance(value, bool) or isinstance(value, float):
        raise InvalidAmountError(
            "Money must be supplied as a Decimal, integer or string."
        )

    try:
        # Convert supported input types into Decimal.
        # Using str() avoids introducing additional float conversion
        # behaviour for accepted input types.
        amount = Decimal(str(value))

    except (InvalidOperation, ValueError):
        raise InvalidAmountError(
            "Enter a valid monetary amount."
        )

    # Reject NaN and positive or negative infinity.
    # Financial operations must only use finite monetary values.
    if not amount.is_finite():
        raise InvalidAmountError(
            "Amount must be a finite number."
        )

    # Normalize the amount to two decimal places.
    # ROUND_HALF_UP rounds midpoint values away from zero.
    amount = amount.quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )

    # Negative monetary values are not accepted for ordinary
    # deposits and withdrawals.
    if amount < 0:
        raise InvalidAmountError(
            "Amount cannot be negative."
        )

    # Deposits and withdrawals normally require a positive amount.
    # Some other operations may explicitly permit zero.
    if not allow_zero and amount == 0:
        raise InvalidAmountError(
            "Amount must be greater than zero."
        )

    return amount


def validate_non_empty(value: str, field_name: str) -> str:
    """
    Validate a required string field and remove surrounding whitespace.

    This utility prevents empty strings and whitespace-only
    values from being accepted as valid application data.

    Args:
        value:
            The string value that needs validation.

        field_name:
            The name of the field being validated.
            Used to produce a descriptive validation error.

    Returns:
        str:
            The validated string with surrounding whitespace removed.

    Raises:
        ValidationError:
            If the supplied value is not a string or contains
            only whitespace.

    Examples:
        >>> validate_non_empty(" LogicBank ", "Project name")
        'LogicBank'

        >>> validate_non_empty("", "Customer name")
        ValidationError
    """

    if not isinstance(value, str) or not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty."
        )

    return value.strip()
