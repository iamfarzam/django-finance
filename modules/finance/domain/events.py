"""Domain events for the finance module.

Events represent facts about what happened in the domain.
They are immutable and used for event-driven communication.
"""

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar
from uuid import UUID

from contracts.events.base import BaseEvent


# =============================================================================
# Account Events
# =============================================================================


class AccountCreated(BaseEvent):
    """Event raised when an account is created."""

    _event_type: ClassVar[str] = "finance.account.created"

    account_id: UUID
    name: str
    account_type: str
    currency_code: str


class AccountUpdated(BaseEvent):
    """Event raised when an account is updated."""

    _event_type: ClassVar[str] = "finance.account.updated"

    account_id: UUID
    updated_fields: list[str]


class AccountClosed(BaseEvent):
    """Event raised when an account is closed."""

    _event_type: ClassVar[str] = "finance.account.closed"

    account_id: UUID
    final_balance: str  # Serialized as string for precision


class AccountReopened(BaseEvent):
    """Event raised when a closed account is reopened."""

    _event_type: ClassVar[str] = "finance.account.reopened"

    account_id: UUID


# =============================================================================
# Transaction Events
# =============================================================================


class TransactionCreated(BaseEvent):
    """Event raised when a transaction is created."""

    _event_type: ClassVar[str] = "finance.transaction.created"

    transaction_id: UUID
    account_id: UUID
    transaction_type: str  # credit or debit
    amount: str  # Decimal serialized as string
    currency_code: str
    description: str | None = None
    category_id: UUID | None = None


class TransactionPosted(BaseEvent):
    """Event raised when a transaction is posted."""

    _event_type: ClassVar[str] = "finance.transaction.posted"

    transaction_id: UUID
    account_id: UUID
    amount: str
    new_balance: str


class TransactionVoided(BaseEvent):
    """Event raised when a transaction is voided."""

    _event_type: ClassVar[str] = "finance.transaction.voided"

    transaction_id: UUID
    account_id: UUID
    reason: str | None = None


class TransactionAdjusted(BaseEvent):
    """Event raised when an adjustment is made to a transaction."""

    _event_type: ClassVar[str] = "finance.transaction.adjusted"

    adjustment_transaction_id: UUID
    original_transaction_id: UUID
    account_id: UUID
    amount: str


# =============================================================================
# Transfer Events
# =============================================================================


class TransferCreated(BaseEvent):
    """Event raised when a transfer is created."""

    _event_type: ClassVar[str] = "finance.transfer.created"

    transfer_id: UUID
    from_account_id: UUID
    to_account_id: UUID
    amount: str
    currency_code: str


class TransferCompleted(BaseEvent):
    """Event raised when a transfer is completed."""

    _event_type: ClassVar[str] = "finance.transfer.completed"

    transfer_id: UUID
    from_transaction_id: UUID
    to_transaction_id: UUID


# =============================================================================
# Asset Events
# =============================================================================


class AssetCreated(BaseEvent):
    """Event raised when an asset is created."""

    _event_type: ClassVar[str] = "finance.asset.created"

    asset_id: UUID
    name: str
    asset_type: str
    current_value: str
    currency_code: str


class AssetValueUpdated(BaseEvent):
    """Event raised when an asset's value is updated."""

    _event_type: ClassVar[str] = "finance.asset.value_updated"

    asset_id: UUID
    old_value: str
    new_value: str
    currency_code: str


class AssetDeleted(BaseEvent):
    """Event raised when an asset is deleted."""

    _event_type: ClassVar[str] = "finance.asset.deleted"

    asset_id: UUID


# =============================================================================
# Liability Events
# =============================================================================


class LiabilityCreated(BaseEvent):
    """Event raised when a liability is created."""

    _event_type: ClassVar[str] = "finance.liability.created"

    liability_id: UUID
    name: str
    liability_type: str
    current_balance: str
    currency_code: str


class LiabilityPaymentRecorded(BaseEvent):
    """Event raised when a payment is recorded on a liability."""

    _event_type: ClassVar[str] = "finance.liability.payment_recorded"

    liability_id: UUID
    payment_amount: str
    new_balance: str


class LiabilityDeleted(BaseEvent):
    """Event raised when a liability is deleted."""

    _event_type: ClassVar[str] = "finance.liability.deleted"

    liability_id: UUID


# =============================================================================
# Loan Events
# =============================================================================


class LoanCreated(BaseEvent):
    """Event raised when a loan is created."""

    _event_type: ClassVar[str] = "finance.loan.created"

    loan_id: UUID
    name: str
    liability_type: str
    original_principal: str
    interest_rate: str
    currency_code: str


class LoanPaymentRecorded(BaseEvent):
    """Event raised when a loan payment is recorded."""

    _event_type: ClassVar[str] = "finance.loan.payment_recorded"

    loan_id: UUID
    principal_amount: str
    interest_amount: str | None
    new_balance: str


class LoanPaidOff(BaseEvent):
    """Event raised when a loan is fully paid off."""

    _event_type: ClassVar[str] = "finance.loan.paid_off"

    loan_id: UUID
    total_paid: str


# =============================================================================
# Category Events
# =============================================================================


class CategoryCreated(BaseEvent):
    """Event raised when a category is created."""

    _event_type: ClassVar[str] = "finance.category.created"

    category_id: UUID
    name: str
    is_income: bool


class CategoryUpdated(BaseEvent):
    """Event raised when a category is updated."""

    _event_type: ClassVar[str] = "finance.category.updated"

    category_id: UUID
    updated_fields: list[str]


class CategoryDeleted(BaseEvent):
    """Event raised when a category is deleted."""

    _event_type: ClassVar[str] = "finance.category.deleted"

    category_id: UUID
