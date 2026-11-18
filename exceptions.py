
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


class CustomerAlreadyExistsError(BankingError):
    """Raised when registering a duplicate customer."""


class CustomerNotFoundError(BankingError):
    """Raised when a customer cannot be found."""


class AccountNotFoundError(BankingError):
    """Raised when an account cannot be found."""


class AccountOwnershipError(AccountError):
    """Raised when a customer tries to access another customer's account."""


class AccountNumberGenerationError(BankingError):
    """Raised when a unique account number cannot be generated."""
