
"""
Customer model for the LogicBank banking application.

This module defines the Customer class, which represents an
individual registered with the banking system.

A customer contains personal identification and contact
information used by the bank to associate accounts with
their rightful owners.

Responsibilities:
    - Store customer identity and contact information.
    - Generate a unique customer ID.
    - Record the customer's registration timestamp.
    - Validate required customer information.
    - Normalize email addresses for consistent identification.

Customer objects are associated with bank accounts through
the account model's owner attribute.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from exceptions import ValidationError
from utils.validators import validate_non_empty


@dataclass
class Customer:
    """
    Represent a registered customer of LogicBank.

    The dataclass automatically generates an initializer and
    other useful methods based on the declared attributes.

    Each customer receives a unique identifier and a UTC
    registration timestamp unless explicitly supplied.

    Attributes:
        full_name:
            The customer's full name.

        email:
            The customer's email address. It is normalized
            to lowercase during initialization.

        phone:
            The customer's contact phone number.
            Defaults to an empty string.

        customer_id:
            A unique identifier generated using UUID4.
            This identifier is used internally to identify
            the customer independently of their email.

        created_at:
            The date and time the customer record was created.
            Defaults to the current UTC timestamp.

    Raises:
        ValidationError:
            If the customer name or email is empty, the email
            fails the model's basic format check, or the phone
            number is not supplied as text.
    """

    full_name: str
    email: str
    phone: str = ""

    # UUID4 provides a randomly generated unique customer identifier.
    customer_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    # Store registration time in UTC to avoid ambiguity between
    # customers registered in different time zones.
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        """
        Validate and normalize customer information after initialization.

        Dataclasses automatically call this method immediately
        after generating the object.

        Validation performed:
            1. Ensure the customer's name is not empty.
            2. Ensure the email is not empty.
            3. Convert the email to lowercase.
            4. Perform a basic email format check.
            5. Ensure the phone number is a string.
            6. Remove surrounding whitespace from the phone number.

        Raises:
            ValidationError:
                If any of the validation rules fail.
        """

        # Customer names are required.
        self.full_name = validate_non_empty(
            self.full_name,
            "Customer name",
        )

        # Normalize email addresses so that different letter
        # casing does not create duplicate customer identities.
        self.email = validate_non_empty(
            self.email,
            "Email",
        ).lower()

        # This is a basic format check, not a complete email
        # address validation implementation.
        if "@" not in self.email or self.email.startswith("@"):
            raise ValidationError(
                "Enter a valid email address."
            )

        # Phone numbers are stored as text because they may
        # contain leading zeros or international prefixes.
        if not isinstance(self.phone, str):
            raise ValidationError(
                "Phone number must be text."
            )

        self.phone = self.phone.strip()

    def display_name(self) -> str:
        """
        Return the customer's full name.

        Returns:
            str: The customer's validated full name.

        This method provides a simple interface for retrieving
        the customer's display name without directly depending
        on how the name is stored internally.
        """

        return self.full_name
