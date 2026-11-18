
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import uuid4

from exceptions import ValidationError
from utils.validators import to_money


class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"


@dataclass(frozen=True)
class Transaction:
    transaction_type: TransactionType
    amount: Decimal
    description: str = ""

    reference: str = field(
        default_factory=lambda: str(uuid4())
    )

    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self):
        if not isinstance(self.transaction_type, TransactionType):
            raise ValidationError("Invalid transaction type.")

        object.__setattr__(
            self,
            "amount",
            to_money(self.amount)
        )

        if not isinstance(self.description, str):
            raise ValidationError("Description must be text.")

    def display(self):
        return (
            f"{self.transaction_type.value}: "
            f"₦{self.amount:,.2f} | "
            f"{self.description}"
        )
