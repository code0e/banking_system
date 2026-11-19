"""
Transaction model for the LogicBank banking application.

This module defines the transaction types and Transaction class
used to represent financial activities performed on bank accounts.

A transaction records an individual financial event, including
its type, monetary amount, description, unique reference and
timestamp.

Responsibilities:
    - Define supported transaction categories.
    - Represent individual financial transactions.
    - Validate transaction types and monetary amounts.
    - Generate unique transaction references.
    - Record transaction timestamps in UTC.
    - Provide a readable transaction representation.

Transaction objects are immutable after creation to help
preserve the integrity of transaction history.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from exceptions import ValidationError
from utils.validators import to_money


class TransactionType(Enum):
    """
    Define the supported transaction categories.

    Enums provide a fixed collection of named values, preventing
    arbitrary transaction type strings from being used throughout
    the banking application.

    Members:
        DEPOSIT:
            Money added to an account.

        WITHDRAWAL:
            Money removed from an account.

        TRANSFER_IN:
            Money received from another bank account.

        TRANSFER_OUT:
            Money sent to another bank account.

    These values are used to classify transaction records and
    distinguish between different financial operations.
    """

    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


@dataclass(frozen=True)
class Transaction:
    """
    Represent an individual financial transaction.

    This class uses a frozen dataclass, meaning its attributes
    cannot be reassigned after the object has been initialized.

    Immutability helps prevent accidental modification of
    transaction records after they have been created.

    Attributes:
        transaction_type:
            The category of transaction, represented by
            a TransactionType enum member.

        amount:
            The monetary value involved in the transaction.
            It is normalized using the shared to_money utility.

        description:
            Optional text describing the transaction.
            Defaults to an empty string.

        reference:
            A unique transaction identifier generated using UUID4.

        timestamp:
            The date and time the transaction was created.
            Defaults to the current UTC timestamp.

    Raises:
        ValidationError:
            If the transaction type is not a TransactionType
            member or the description is not a string.

        InvalidAmountError:
            If the transaction amount fails monetary validation.
    """

    transaction_type: TransactionType
    amount: Decimal
    description: str = ""

    # Every transaction receives its own unique reference.
    # UUID4 reduces the risk of reference collisions.
    reference: str = field(
        default_factory=lambda: str(uuid4())
    )

    # Store transaction creation time in UTC.
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """
        Validate transaction data after initialization.

        Because this dataclass is frozen, normal attribute
        assignment is not permitted inside this method.

        object.__setattr__ is therefore used to replace the
        supplied amount with its validated Decimal equivalent.

        Validation performed:
            1. Confirm that the transaction type is valid.
            2. Normalize and validate the monetary amount.
            3. Confirm that the description is text.

        Raises:
            ValidationError:
                If the transaction type or description is invalid.

            InvalidAmountError:
                If the amount is invalid, negative or zero.
        """

        if not isinstance(
            self.transaction_type,
            TransactionType,
        ):
            raise ValidationError(
                "Invalid transaction type."
            )

        # Frozen dataclasses prevent ordinary assignment.
        # This controlled assignment stores the normalized
        # monetary value while preserving immutability afterward.
        object.__setattr__(
            self,
            "amount",
            to_money(self.amount),
        )

        if not isinstance(self.description, str):
            raise ValidationError(
                "Description must be text."
            )

    def display(self) -> str:
        """
        Return a human-readable representation of the transaction.

        Returns:
            str: A formatted string containing the transaction
            type, amount and description.

        The amount is displayed using NGN and two decimal places
        for consistency with LogicBank's monetary presentation.
        """

        return (
            f"{self.transaction_type.value}: "
            f"NGN {self.amount:,.2f} | "
            f"{self.description}"
        )
