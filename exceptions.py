
class BankingError(Exception):
    """Base exception for LogicBank."""


class ValidationError(BankingError):
    """Raised when supplied data is invalid."""


class InvalidAmountError(ValidationError):
    """Raised when a monetary amount is invalid."""


class InsufficientFundsError(BankingError):
    """Raised when an account cannot cover a withdrawal."""


class MinimumBalanceError(BankingError):
    """Raised when a withdrawal violates minimum balance rules."""


class AccountError(BankingError):
    """Raised when an account operation is invalid."""
