
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from exceptions import ValidationError
from utils.validators import validate_non_empty


@dataclass
class Customer:
    full_name: str
    email: str
    phone: str = ""

    customer_id: str = field(
        default_factory=lambda: str(uuid4())
    )

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        self.full_name = validate_non_empty(
            self.full_name, "Customer name"
        )

        self.email = validate_non_empty(
            self.email, "Email"
        ).lower()

        if "@" not in self.email or self.email.startswith("@"):
            raise ValidationError("Enter a valid email address.")

        if not isinstance(self.phone, str):
            raise ValidationError("Phone number must be text.")

        self.phone = self.phone.strip()

    def display_name(self):
        return self.full_name
