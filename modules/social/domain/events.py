"""Domain events for the social finance module.

These events represent significant occurrences in the domain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from contracts.events.base import BaseEvent


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


# =============================================================================
# Contact Events
# =============================================================================


@dataclass
class ContactCreated(BaseEvent):
    """Event raised when a new contact is created."""

    event_type: str = field(default="contact.created", init=False)
    contact_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    email: str | None = None


@dataclass
class ContactUpdated(BaseEvent):
    """Event raised when a contact is updated."""

    event_type: str = field(default="contact.updated", init=False)
    contact_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    changes: dict = field(default_factory=dict)


@dataclass
class ContactArchived(BaseEvent):
    """Event raised when a contact is archived."""

    event_type: str = field(default="contact.archived", init=False)
    contact_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)


@dataclass
class ContactLinkedToUser(BaseEvent):
    """Event raised when a contact is linked to a registered user."""

    event_type: str = field(default="contact.linked", init=False)
    contact_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    linked_user_id: UUID = field(default_factory=uuid4)


@dataclass
class ShareInvitationSent(BaseEvent):
    """Event raised when a sharing invitation is sent."""

    event_type: str = field(default="contact.share_invited", init=False)
    contact_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    invited_user_id: UUID = field(default_factory=uuid4)


@dataclass
class ShareInvitationAccepted(BaseEvent):
    """Event raised when a sharing invitation is accepted."""

    event_type: str = field(default="contact.share_accepted", init=False)
    contact_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    accepted_user_id: UUID = field(default_factory=uuid4)


# =============================================================================
# Peer Debt Events
# =============================================================================


@dataclass
class PeerDebtCreated(BaseEvent):
    """Event raised when a new peer debt is created."""

    event_type: str = field(default="peer_debt.created", init=False)
    debt_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    contact_id: UUID = field(default_factory=uuid4)
    direction: str = ""  # "lent" or "borrowed"
    amount: Decimal = Decimal("0")
    currency_code: str = ""


@dataclass
class PeerDebtSettled(BaseEvent):
    """Event raised when a peer debt is partially or fully settled."""

    event_type: str = field(default="peer_debt.settled", init=False)
    debt_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    settlement_amount: Decimal = Decimal("0")
    remaining_amount: Decimal = Decimal("0")
    is_fully_settled: bool = False


@dataclass
class PeerDebtCancelled(BaseEvent):
    """Event raised when a peer debt is cancelled/forgiven."""

    event_type: str = field(default="peer_debt.cancelled", init=False)
    debt_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)


# =============================================================================
# Expense Group Events
# =============================================================================


@dataclass
class ExpenseGroupCreated(BaseEvent):
    """Event raised when a new expense group is created."""

    event_type: str = field(default="expense_group.created", init=False)
    group_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    name: str = ""
    member_count: int = 0


@dataclass
class ExpenseGroupMemberAdded(BaseEvent):
    """Event raised when a member is added to an expense group."""

    event_type: str = field(default="expense_group.member_added", init=False)
    group_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    contact_id: UUID = field(default_factory=uuid4)


@dataclass
class ExpenseGroupMemberRemoved(BaseEvent):
    """Event raised when a member is removed from an expense group."""

    event_type: str = field(default="expense_group.member_removed", init=False)
    group_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    contact_id: UUID = field(default_factory=uuid4)


# =============================================================================
# Group Expense Events
# =============================================================================


@dataclass
class GroupExpenseCreated(BaseEvent):
    """Event raised when a new group expense is created."""

    event_type: str = field(default="group_expense.created", init=False)
    expense_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    group_id: UUID = field(default_factory=uuid4)
    description: str = ""
    total_amount: Decimal = Decimal("0")
    currency_code: str = ""
    split_count: int = 0


@dataclass
class GroupExpenseUpdated(BaseEvent):
    """Event raised when a group expense is updated."""

    event_type: str = field(default="group_expense.updated", init=False)
    expense_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    changes: dict = field(default_factory=dict)


@dataclass
class GroupExpenseCancelled(BaseEvent):
    """Event raised when a group expense is cancelled."""

    event_type: str = field(default="group_expense.cancelled", init=False)
    expense_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)


@dataclass
class ExpenseSplitSettled(BaseEvent):
    """Event raised when an expense split is settled."""

    event_type: str = field(default="expense_split.settled", init=False)
    split_id: UUID = field(default_factory=uuid4)
    expense_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    settlement_amount: Decimal = Decimal("0")
    is_fully_settled: bool = False


# =============================================================================
# Settlement Events
# =============================================================================


@dataclass
class SettlementCreated(BaseEvent):
    """Event raised when a settlement is recorded."""

    event_type: str = field(default="settlement.created", init=False)
    settlement_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    from_is_owner: bool = False
    to_is_owner: bool = False
    from_contact_id: UUID | None = None
    to_contact_id: UUID | None = None
    amount: Decimal = Decimal("0")
    currency_code: str = ""
    linked_debt_count: int = 0
    linked_split_count: int = 0


@dataclass
class BalanceUpdated(BaseEvent):
    """Event raised when balance with a contact changes."""

    event_type: str = field(default="balance.updated", init=False)
    tenant_id: UUID = field(default_factory=uuid4)
    contact_id: UUID = field(default_factory=uuid4)
    currency_code: str = ""
    new_balance: Decimal = Decimal("0")
    balance_direction: str = ""  # "they_owe_you" or "you_owe_them"
