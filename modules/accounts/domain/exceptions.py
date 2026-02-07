"""Domain exceptions for the accounts module.

These exceptions represent business rule violations specific to
user accounts and authentication.
"""

from __future__ import annotations

from shared.exceptions import AuthorizationError, DomainError, DomainValidationError


class AccountError(DomainError):
    """Base exception for account-related errors."""

    pass


class UserNotFoundError(AccountError):
    """User was not found."""

    def __init__(self, identifier: str) -> None:
        super().__init__(
            message=f"User not found: {identifier}",
            code="USER_NOT_FOUND",
        )


class EmailAlreadyExistsError(AccountError):
    """Email address is already registered."""

    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"Email already registered: {email}",
            code="EMAIL_ALREADY_EXISTS",
        )


class InvalidCredentialsError(AccountError):
    """Invalid login credentials."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password",
            code="INVALID_CREDENTIALS",
        )


class AccountLockedError(AccountError):
    """Account is locked due to too many failed attempts."""

    def __init__(self, locked_until: str | None = None) -> None:
        message = "Account is locked due to too many failed login attempts"
        if locked_until:
            message += f". Try again after {locked_until}"
        super().__init__(message=message, code="ACCOUNT_LOCKED")


class AccountNotActiveError(AccountError):
    """Account is not in active status."""

    def __init__(self, status: str) -> None:
        super().__init__(
            message=f"Account is not active. Current status: {status}",
            code="ACCOUNT_NOT_ACTIVE",
        )


class EmailNotVerifiedError(AccountError):
    """Email address has not been verified."""

    def __init__(self) -> None:
        super().__init__(
            message="Email address has not been verified",
            code="EMAIL_NOT_VERIFIED",
        )


class InvalidTokenError(AccountError):
    """Token is invalid or expired."""

    def __init__(self, token_type: str = "token") -> None:
        super().__init__(
            message=f"Invalid or expired {token_type}",
            code="INVALID_TOKEN",
        )


class PasswordValidationError(DomainValidationError):
    """Password does not meet requirements."""

    def __init__(self, message: str, details: list | None = None) -> None:
        super().__init__(
            message=message,
            field="password",
            details=details or [],
        )


class PasswordPolicyError(PasswordValidationError):
    """Password does not meet policy requirements."""

    def __init__(self, violations: list[str]) -> None:
        details = [{"field": "password", "message": v} for v in violations]
        super().__init__(
            message="Password does not meet security requirements",
            details=details,
        )


class TokenExpiredError(InvalidTokenError):
    """Token has expired."""

    def __init__(self, token_type: str = "token") -> None:
        super().__init__(token_type)
        self.code = "TOKEN_EXPIRED"


class RateLimitExceededError(AccountError):
    """Rate limit has been exceeded."""

    def __init__(self, retry_after: int | None = None) -> None:
        message = "Too many requests. Please try again later"
        if retry_after:
            message += f" (retry after {retry_after} seconds)"
        super().__init__(message=message, code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after
