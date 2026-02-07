"""Domain exceptions for the finance module.

These exceptions represent domain-level errors and are framework-agnostic.
They should be caught and translated to appropriate HTTP responses at the
interface layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class FinanceDomainError(Exception):
    """Base exception for all finance domain errors."""

    pass


class AccountNotFoundError(FinanceDomainError):
    """Raised when an account is not found."""

    def __init__(self, account_id: UUID | str) -> None:
        self.account_id = account_id
        super().__init__(f"Account not found: {account_id}")


class AccountClosedError(FinanceDomainError):
    """Raised when attempting to operate on a closed account."""

    def __init__(self, account_id: UUID | str) -> None:
        self.account_id = account_id
        super().__init__(f"Account is closed: {account_id}")


class AccountLimitExceededError(FinanceDomainError):
    """Raised when user exceeds account limit for their tier."""

    def __init__(self, limit: int, current: int) -> None:
        self.limit = limit
        self.current = current
        super().__init__(
            f"Account limit exceeded: {current} accounts, limit is {limit}"
        )


class TransactionNotFoundError(FinanceDomainError):
    """Raised when a transaction is not found."""

    def __init__(self, transaction_id: UUID | str) -> None:
        self.transaction_id = transaction_id
        super().__init__(f"Transaction not found: {transaction_id}")


class TransactionImmutableError(FinanceDomainError):
    """Raised when attempting to modify an immutable transaction."""

    def __init__(self, transaction_id: UUID | str) -> None:
        self.transaction_id = transaction_id
        super().__init__(
            f"Transaction is immutable and cannot be modified: {transaction_id}"
        )


class TransactionVoidedError(FinanceDomainError):
    """Raised when attempting to operate on a voided transaction."""

    def __init__(self, transaction_id: UUID | str) -> None:
        self.transaction_id = transaction_id
        super().__init__(f"Transaction has been voided: {transaction_id}")


class InvalidAmountError(FinanceDomainError):
    """Raised when a monetary amount is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CurrencyMismatchError(FinanceDomainError):
    """Raised when currencies don't match for an operation."""

    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"Currency mismatch: expected {expected}, got {actual}"
        )


class UnsupportedCurrencyError(FinanceDomainError):
    """Raised when a currency is not supported."""

    def __init__(self, currency_code: str) -> None:
        self.currency_code = currency_code
        super().__init__(f"Unsupported currency: {currency_code}")


class InsufficientBalanceError(FinanceDomainError):
    """Raised when account balance is insufficient for an operation."""

    def __init__(
        self, account_id: UUID | str, required: str, available: str
    ) -> None:
        self.account_id = account_id
        self.required = required
        self.available = available
        super().__init__(
            f"Insufficient balance in account {account_id}: "
            f"required {required}, available {available}"
        )


class AssetNotFoundError(FinanceDomainError):
    """Raised when an asset is not found."""

    def __init__(self, asset_id: UUID | str) -> None:
        self.asset_id = asset_id
        super().__init__(f"Asset not found: {asset_id}")


class LiabilityNotFoundError(FinanceDomainError):
    """Raised when a liability is not found."""

    def __init__(self, liability_id: UUID | str) -> None:
        self.liability_id = liability_id
        super().__init__(f"Liability not found: {liability_id}")


class LoanNotFoundError(FinanceDomainError):
    """Raised when a loan is not found."""

    def __init__(self, loan_id: UUID | str) -> None:
        self.loan_id = loan_id
        super().__init__(f"Loan not found: {loan_id}")


class LoanAlreadyPaidOffError(FinanceDomainError):
    """Raised when attempting to pay on an already paid off loan."""

    def __init__(self, loan_id: UUID | str) -> None:
        self.loan_id = loan_id
        super().__init__(f"Loan has already been paid off: {loan_id}")


class IdempotencyKeyExistsError(FinanceDomainError):
    """Raised when an idempotency key has already been used."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Idempotency key already exists: {key}")


class CategoryNotFoundError(FinanceDomainError):
    """Raised when a category is not found."""

    def __init__(self, category_id: UUID | str) -> None:
        self.category_id = category_id
        super().__init__(f"Category not found: {category_id}")


class InvalidDateRangeError(FinanceDomainError):
    """Raised when a date range is invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class TransferSameAccountError(FinanceDomainError):
    """Raised when attempting to transfer to the same account."""

    def __init__(self, account_id: UUID | str) -> None:
        self.account_id = account_id
        super().__init__(
            f"Cannot transfer to the same account: {account_id}"
        )
