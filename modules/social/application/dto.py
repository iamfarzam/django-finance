"""Data Transfer Objects for the social finance module."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# =============================================================================
# Contact DTOs
# =============================================================================


@dataclass
class ContactDTO:
    """DTO for Contact entity."""

    id: UUID
    tenant_id: UUID
    name: str
    email: str | None
    phone: str | None
    avatar_url: str | None
    notes: str | None
    status: str
    linked_user_id: UUID | None
    share_status: str
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateContactCommand:
    """Command for creating a contact."""

    tenant_id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


@dataclass
class UpdateContactCommand:
    """Command for updating a contact."""

    contact_id: UUID
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None


# =============================================================================
# Contact Group DTOs
# =============================================================================


@dataclass
class ContactGroupDTO:
    """DTO for ContactGroup entity."""

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    member_ids: list[UUID]
    member_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateContactGroupCommand:
    """Command for creating a contact group."""

    tenant_id: UUID
    name: str
    description: str | None = None
    member_ids: list[UUID] = field(default_factory=list)


# =============================================================================
# Peer Debt DTOs
# =============================================================================


@dataclass
class PeerDebtDTO:
    """DTO for PeerDebt entity."""

    id: UUID
    tenant_id: UUID
    contact_id: UUID
    contact_name: str | None  # Denormalized for display
    direction: str
    amount: Decimal
    currency_code: str
    settled_amount: Decimal
    remaining_amount: Decimal
    description: str | None
    debt_date: date
    due_date: date | None
    status: str
    linked_transaction_id: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class CreatePeerDebtCommand:
    """Command for creating a peer debt."""

    tenant_id: UUID
    contact_id: UUID
    direction: str  # "lent" or "borrowed"
    amount: Decimal
    currency_code: str
    description: str | None = None
    debt_date: date | None = None
    due_date: date | None = None
    notes: str | None = None
    linked_transaction_id: UUID | None = None


@dataclass
class SettleDebtCommand:
    """Command for settling a peer debt."""

    debt_id: UUID
    amount: Decimal
    settlement_id: UUID | None = None  # Link to Settlement if applicable


# =============================================================================
# Expense Group DTOs
# =============================================================================


@dataclass
class ExpenseGroupDTO:
    """DTO for ExpenseGroup entity."""

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None
    default_currency: str
    member_contact_ids: list[UUID]
    include_self: bool
    total_members: int
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateExpenseGroupCommand:
    """Command for creating an expense group."""

    tenant_id: UUID
    name: str
    default_currency: str = "USD"
    description: str | None = None
    member_contact_ids: list[UUID] = field(default_factory=list)
    include_self: bool = True


# =============================================================================
# Group Expense DTOs
# =============================================================================


@dataclass
class ExpenseSplitDTO:
    """DTO for ExpenseSplit entity."""

    id: UUID
    expense_id: UUID
    contact_id: UUID | None
    is_owner: bool
    share_amount: Decimal
    settled_amount: Decimal
    remaining_amount: Decimal
    status: str


@dataclass
class GroupExpenseDTO:
    """DTO for GroupExpense entity."""

    id: UUID
    tenant_id: UUID
    group_id: UUID
    description: str
    total_amount: Decimal
    currency_code: str
    paid_by_contact_id: UUID | None
    paid_by_owner: bool
    split_method: str
    expense_date: date
    splits: list[ExpenseSplitDTO]
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class CreateGroupExpenseCommand:
    """Command for creating a group expense."""

    tenant_id: UUID
    group_id: UUID
    description: str
    total_amount: Decimal
    currency_code: str
    paid_by_owner: bool = True
    paid_by_contact_id: UUID | None = None
    split_method: str = "equal"
    expense_date: date | None = None
    notes: str | None = None
    # For exact splits: contact_id -> amount (None key = owner)
    exact_splits: dict[UUID | None, Decimal] | None = None


# =============================================================================
# Settlement DTOs
# =============================================================================


@dataclass
class SettlementDTO:
    """DTO for Settlement entity."""

    id: UUID
    tenant_id: UUID
    from_contact_id: UUID | None
    to_contact_id: UUID | None
    from_is_owner: bool
    to_is_owner: bool
    amount: Decimal
    currency_code: str
    method: str
    settlement_date: date
    linked_debt_ids: list[UUID]
    linked_split_ids: list[UUID]
    notes: str | None
    created_at: datetime


@dataclass
class CreateSettlementCommand:
    """Command for creating a settlement."""

    tenant_id: UUID
    amount: Decimal
    currency_code: str
    # One of these must be True
    owner_pays: bool = False  # Owner pays contact
    owner_receives: bool = False  # Owner receives from contact
    # The contact involved
    contact_id: UUID | None = None
    method: str = "cash"
    settlement_date: date | None = None
    notes: str | None = None
    # Optional links to what this settlement covers
    linked_debt_ids: list[UUID] = field(default_factory=list)
    linked_split_ids: list[UUID] = field(default_factory=list)


# =============================================================================
# Balance DTOs
# =============================================================================


@dataclass
class ContactBalanceDTO:
    """DTO for contact balance."""

    contact_id: UUID
    contact_name: str | None
    currency_code: str
    total_lent: Decimal
    total_borrowed: Decimal
    total_settled_to_them: Decimal
    total_settled_from_them: Decimal
    net_balance: Decimal
    they_owe_you: Decimal
    you_owe_them: Decimal


@dataclass
class GroupBalanceEntryDTO:
    """DTO for a group balance entry."""

    from_contact_id: UUID | None
    from_name: str | None  # None or "You" for owner
    to_contact_id: UUID | None
    to_name: str | None  # None or "You" for owner
    amount: Decimal


@dataclass
class GroupBalanceDTO:
    """DTO for group balance."""

    group_id: UUID
    group_name: str
    currency_code: str
    entries: list[GroupBalanceEntryDTO]
    total_expenses: Decimal


@dataclass
class SettlementSuggestionDTO:
    """DTO for settlement suggestion."""

    from_contact_id: UUID | None
    from_name: str | None
    to_contact_id: UUID | None
    to_name: str | None
    amount: Decimal
    currency_code: str
