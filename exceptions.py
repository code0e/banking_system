"""
Custom exception definitions for the LogicBank application.

This module centralizes application-specific exceptions used
throughout the banking system.

The exception hierarchy allows different parts of the application
to handle related errors consistently.

Exception hierarchy:

    Exception
        └── BankingError
            ├── ValidationError
            │   └── InvalidAmountError
            ├── InsufficientFundsError
            ├── MinimumBalanceError
            ├── AccountError
            │   └── AccountOwnershipError
            ├── CustomerAlreadyExistsError
            ├── CustomerNotFoundError
            ├── AccountNotFoundError
            └── AccountNumberGenerationError

All custom application exceptions inherit from BankingError,
directly or indirectly.
"""


class BankingError(Exception):
    """
    Base exception for all LogicBank application errors.

    All custom exceptions raised by the banking system should
    inherit from this class.

    This allows callers to catch general banking errors without
    needing to handle every specific exception individually.

    Example:
        try:
            bank.deposit(account_number, amount)
        except BankingError as error:
            print(f"Banking operation failed: {error}")
    """


class ValidationError(BankingError):
    """
    Raised when supplied application data fails validation.

    This exception is intended for invalid input that does not
    necessarily involve a monetary amount.

    Examples:
        - Empty customer names.
        - Invalid required string fields.
        - Missing or improperly formatted input.
    """


class InvalidAmountError(ValidationError):
    """
    Raised when a monetary amount is invalid.

    This exception is used when an amount fails financial
    validation rules.

    Examples:
        - Negative deposit or withdrawal amounts.
        - Zero amounts when a positive amount is required.
        - Floating-point values supplied for monetary operations.
        - Non-numeric or non-finite monetary values.
    """


class InsufficientFundsError(BankingError):
    """
    Raised when an account cannot cover a requested withdrawal.

    This exception is typically raised when a withdrawal would
    exceed the available balance and any permitted overdraft.

    The account balance must remain unchanged when the withdrawal
    fails.
    """


class MinimumBalanceError(BankingError):
    """
    Raised when a withdrawal violates savings account rules.

    Savings accounts may require a minimum balance to remain
    after a withdrawal.

    This exception indicates that the requested withdrawal would
    cause the account balance to fall below that minimum.
    """


class AccountError(BankingError):
    """
    Base exception for account-related operation failures.

    This class provides a common exception type for errors
    involving account operations and account-specific rules.
    """


class CustomerAlreadyExistsError(BankingError):
    """
    Raised when attempting to register an existing customer.

    LogicBank uses customer email addresses as unique identifiers
    for duplicate registration checks.

    This exception is raised when the supplied email address
    already belongs to a registered customer.
    """


class CustomerNotFoundError(BankingError):
    """
    Raised when a requested customer does not exist.

    This exception may occur when retrieving a customer using
    an unknown customer ID or email address.
    """


class AccountNotFoundError(BankingError):
    """
    Raised when a requested bank account does not exist.

    This exception is used when an account lookup fails,
    such as when retrieving an account using an unknown
    account number.
    """


class AccountOwnershipError(AccountError):
    """
    Raised when a customer attempts to access another customer's account.

    LogicBank must verify account ownership before allowing
    customer-authorized operations.

    Examples:
        - Depositing into another customer's account.
        - Withdrawing from another customer's account.
        - Retrieving another customer's transaction history.
    """


class AccountNumberGenerationError(BankingError):
    """
    Raised when a unique bank account number cannot be generated.

    Account numbers must be unique across all accounts managed
    by the bank service.

    This exception is raised when the account number generation
    process exhausts its permitted attempts without finding
    an unused number.
    """


class AuthenticationError(BankingError):
    """Base exception for authentication and session failures."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when an email/password pair cannot be authenticated."""


class WeakPasswordError(ValidationError):
    """Raised when a password does not meet the application's policy."""


class SessionNotFoundError(AuthenticationError):
    """Raised when a session token is missing, invalid, or logged out."""



class AuthenticationRateLimitError(AuthenticationError):
    """Raised when repeated failed logins temporarily block an email."""
