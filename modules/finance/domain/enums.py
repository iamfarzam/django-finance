"""Domain enumerations for the finance module."""

from __future__ import annotations

from enum import Enum


class TransactionType(str, Enum):
    """Transaction type indicating money flow direction.

    In single-entry accounting:
    - CREDIT: Money coming in (increases balance)
    - DEBIT: Money going out (decreases balance)
    """

    CREDIT = "credit"
    DEBIT = "debit"

    @property
    def sign(self) -> int:
        """Return the sign for balance calculation."""
        return 1 if self == TransactionType.CREDIT else -1


class AccountType(str, Enum):
    """Types of financial accounts."""

    CHECKING = "checking"
    SAVINGS = "savings"
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    INVESTMENT = "investment"
    WALLET = "wallet"
    OTHER = "other"


class AccountStatus(str, Enum):
    """Status of a financial account."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CLOSED = "closed"


class TransactionStatus(str, Enum):
    """Status of a transaction."""

    PENDING = "pending"
    POSTED = "posted"
    VOIDED = "voided"


class AssetType(str, Enum):
    """Types of assets."""

    REAL_ESTATE = "real_estate"
    VEHICLE = "vehicle"
    INVESTMENT = "investment"
    COLLECTIBLE = "collectible"
    RECEIVABLE = "receivable"
    OTHER = "other"


class LiabilityType(str, Enum):
    """Types of liabilities."""

    MORTGAGE = "mortgage"
    AUTO_LOAN = "auto_loan"
    PERSONAL_LOAN = "personal_loan"
    STUDENT_LOAN = "student_loan"
    CREDIT_CARD = "credit_card"
    LINE_OF_CREDIT = "line_of_credit"
    OTHER = "other"


class LoanStatus(str, Enum):
    """Status of a loan."""

    ACTIVE = "active"
    PAID_OFF = "paid_off"
    DEFAULTED = "defaulted"
    DEFERRED = "deferred"


class PaymentFrequency(str, Enum):
    """Payment frequency for loans."""

    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class RecurrencePattern(str, Enum):
    """Recurrence patterns for scheduled transactions."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
