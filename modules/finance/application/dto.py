"""Data Transfer Objects for the finance module.

DTOs are used for communication between layers and with external systems.
They are simple data containers without business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# =============================================================================
# Account DTOs
# =============================================================================


@dataclass(frozen=True)
class AccountDTO:
    """Data transfer object for Account entity."""

    id: UUID
    tenant_id: UUID
    name: str
    account_type: str
    currency_code: str
    status: str
    institution: str | None
    account_number_masked: str | None
    notes: str | None
    is_included_in_net_worth: bool
    display_order: int
    created_at: datetime
    updated_at: datetime
    # Computed fields
    balance: Decimal | None = None
    formatted_balance: str | None = None


@dataclass(frozen=True)
class CreateAccountCommand:
    """Command to create a new account."""

    tenant_id: UUID
    name: str
    account_type: str
    currency_code: str
    institution: str | None = None
    account_number_masked: str | None = None
    notes: str | None = None
    initial_balance: Decimal | None = None


@dataclass(frozen=True)
class UpdateAccountCommand:
    """Command to update an account."""

    account_id: UUID
    tenant_id: UUID
    name: str | None = None
    institution: str | None = None
    notes: str | None = None
    is_included_in_net_worth: bool | None = None


# =============================================================================
# Transaction DTOs
# =============================================================================


@dataclass(frozen=True)
class TransactionDTO:
    """Data transfer object for Transaction entity."""

    id: UUID
    tenant_id: UUID
    account_id: UUID
    transaction_type: str
    amount: Decimal
    currency_code: str
    status: str
    transaction_date: date
    posted_at: datetime | None
    description: str
    category_id: UUID | None
    category_name: str | None
    reference_number: str | None
    notes: str | None
    is_adjustment: bool
    adjustment_for_id: UUID | None
    created_at: datetime
    updated_at: datetime
    # Computed fields
    signed_amount: Decimal | None = None
    formatted_amount: str | None = None
    running_balance: Decimal | None = None


@dataclass(frozen=True)
class CreateTransactionCommand:
    """Command to create a new transaction."""

    tenant_id: UUID
    account_id: UUID
    transaction_type: str  # "credit" or "debit"
    amount: Decimal
    currency_code: str
    description: str = ""
    transaction_date: date | None = None
    category_id: UUID | None = None
    reference_number: str | None = None
    notes: str | None = None
    idempotency_key: str | None = None
    auto_post: bool = True


@dataclass(frozen=True)
class VoidTransactionCommand:
    """Command to void a transaction."""

    transaction_id: UUID
    tenant_id: UUID
    reason: str | None = None


@dataclass(frozen=True)
class AdjustTransactionCommand:
    """Command to create an adjustment for a transaction."""

    original_transaction_id: UUID
    tenant_id: UUID
    new_amount: Decimal | None = None
    new_type: str | None = None
    notes: str | None = None


# =============================================================================
# Transfer DTOs
# =============================================================================


@dataclass(frozen=True)
class TransferDTO:
    """Data transfer object for Transfer."""

    id: UUID
    tenant_id: UUID
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal
    currency_code: str
    from_transaction_id: UUID | None
    to_transaction_id: UUID | None
    transfer_date: date
    description: str
    notes: str | None
    created_at: datetime


@dataclass(frozen=True)
class CreateTransferCommand:
    """Command to create a transfer between accounts."""

    tenant_id: UUID
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal
    currency_code: str
    transfer_date: date | None = None
    description: str = ""
    notes: str | None = None
    idempotency_key: str | None = None


# =============================================================================
# Asset DTOs
# =============================================================================


@dataclass(frozen=True)
class AssetDTO:
    """Data transfer object for Asset entity."""

    id: UUID
    tenant_id: UUID
    name: str
    asset_type: str
    current_value: Decimal
    currency_code: str
    purchase_date: date | None
    purchase_price: Decimal | None
    description: str | None
    notes: str | None
    is_included_in_net_worth: bool
    created_at: datetime
    updated_at: datetime
    # Computed fields
    formatted_value: str | None = None
    gain_loss: Decimal | None = None


@dataclass(frozen=True)
class CreateAssetCommand:
    """Command to create a new asset."""

    tenant_id: UUID
    name: str
    asset_type: str
    current_value: Decimal
    currency_code: str
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    description: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class UpdateAssetValueCommand:
    """Command to update an asset's value."""

    asset_id: UUID
    tenant_id: UUID
    new_value: Decimal


# =============================================================================
# Liability DTOs
# =============================================================================


@dataclass(frozen=True)
class LiabilityDTO:
    """Data transfer object for Liability entity."""

    id: UUID
    tenant_id: UUID
    name: str
    liability_type: str
    current_balance: Decimal
    currency_code: str
    interest_rate: Decimal | None
    minimum_payment: Decimal | None
    due_day: int | None
    creditor: str | None
    account_number_masked: str | None
    notes: str | None
    is_included_in_net_worth: bool
    created_at: datetime
    updated_at: datetime
    # Computed fields
    formatted_balance: str | None = None


@dataclass(frozen=True)
class CreateLiabilityCommand:
    """Command to create a new liability."""

    tenant_id: UUID
    name: str
    liability_type: str
    current_balance: Decimal
    currency_code: str
    interest_rate: Decimal | None = None
    minimum_payment: Decimal | None = None
    due_day: int | None = None
    creditor: str | None = None
    account_number_masked: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class RecordLiabilityPaymentCommand:
    """Command to record a payment on a liability."""

    liability_id: UUID
    tenant_id: UUID
    payment_amount: Decimal


# =============================================================================
# Loan DTOs
# =============================================================================


@dataclass(frozen=True)
class LoanDTO:
    """Data transfer object for Loan entity."""

    id: UUID
    tenant_id: UUID
    name: str
    liability_type: str
    original_principal: Decimal
    current_balance: Decimal
    currency_code: str
    interest_rate: Decimal
    payment_amount: Decimal
    payment_frequency: str
    status: str
    start_date: date | None
    expected_payoff_date: date | None
    next_payment_date: date | None
    lender: str | None
    account_number_masked: str | None
    notes: str | None
    linked_account_id: UUID | None
    is_included_in_net_worth: bool
    created_at: datetime
    updated_at: datetime
    # Computed fields
    formatted_balance: str | None = None
    principal_paid: Decimal | None = None
    principal_paid_percentage: Decimal | None = None


@dataclass(frozen=True)
class CreateLoanCommand:
    """Command to create a new loan."""

    tenant_id: UUID
    name: str
    liability_type: str
    principal: Decimal
    currency_code: str
    interest_rate: Decimal
    payment_amount: Decimal
    payment_frequency: str
    start_date: date | None = None
    expected_payoff_date: date | None = None
    next_payment_date: date | None = None
    lender: str | None = None
    account_number_masked: str | None = None
    notes: str | None = None
    linked_account_id: UUID | None = None


@dataclass(frozen=True)
class RecordLoanPaymentCommand:
    """Command to record a loan payment."""

    loan_id: UUID
    tenant_id: UUID
    principal_amount: Decimal
    interest_amount: Decimal | None = None


# =============================================================================
# Category DTOs
# =============================================================================


@dataclass(frozen=True)
class CategoryDTO:
    """Data transfer object for Category entity."""

    id: UUID
    tenant_id: UUID
    name: str
    parent_id: UUID | None
    icon: str | None
    color: str | None
    is_system: bool
    is_income: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class CreateCategoryCommand:
    """Command to create a new category."""

    tenant_id: UUID
    name: str
    parent_id: UUID | None = None
    icon: str | None = None
    color: str | None = None
    is_income: bool = False


# =============================================================================
# Report DTOs
# =============================================================================


@dataclass(frozen=True)
class NetWorthDTO:
    """Data transfer object for net worth report."""

    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    account_balances: Decimal
    asset_count: int
    liability_count: int
    account_count: int
    currency_code: str
    calculated_at: datetime


@dataclass(frozen=True)
class CashFlowDTO:
    """Data transfer object for cash flow report."""

    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    income_by_category: dict[str, Decimal]
    expenses_by_category: dict[str, Decimal]
    currency_code: str
    start_date: date
    end_date: date


@dataclass(frozen=True)
class BalanceDTO:
    """Data transfer object for account balance."""

    account_id: UUID
    balance: Decimal
    total_credits: Decimal
    total_debits: Decimal
    transaction_count: int
    currency_code: str
    as_of_date: date | None = None
