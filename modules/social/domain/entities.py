"""Domain entities for the social finance module.

These are pure Python domain objects with business logic.
They have no dependencies on Django or other frameworks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from modules.social.domain.enums import (
    ContactStatus,
    DebtDirection,
    DebtStatus,
    ExpenseStatus,
    SettlementMethod,
    ShareStatus,
    SplitMethod,
    SplitStatus,
)

if TYPE_CHECKING:
    from modules.finance.domain.value_objects import Money


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


@dataclass
class Contact:
    """A contact (friend, family member, etc.) for social finance features.

    Contacts can be:
    - Independent: Just a name/details stored by the owner
    - Linked: Associated with a registered user account

    Attributes:
        id: Unique identifier.
        tenant_id: Owner's tenant ID.
        name: Display name of the contact.
        email: Optional email address.
        phone: Optional phone number.
        avatar_url: Optional avatar image URL.
        notes: Optional notes about the contact.
        status: Contact status (active, archived).
        linked_user_id: If linked to a registered user, their user ID.
        share_status: Status of sharing with linked user.
        created_at: When the contact was created.
        updated_at: When the contact was last updated.
    """

    id: UUID
    tenant_id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    notes: str | None = None
    status: ContactStatus = ContactStatus.ACTIVE
    linked_user_id: UUID | None = None
    share_status: ShareStatus = ShareStatus.NOT_SHARED
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> Contact:
        """Create a new contact.

        Args:
            tenant_id: Owner's tenant ID.
            name: Display name.
            email: Optional email.
            phone: Optional phone.
            notes: Optional notes.

        Returns:
            New Contact instance.
        """
        if not name or not name.strip():
            raise ValueError("Contact name is required")

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name.strip(),
            email=email.strip() if email else None,
            phone=phone.strip() if phone else None,
            notes=notes,
        )

    def update(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> None:
        """Update contact details."""
        if name is not None:
            if not name.strip():
                raise ValueError("Contact name cannot be empty")
            self.name = name.strip()
        if email is not None:
            self.email = email.strip() if email else None
        if phone is not None:
            self.phone = phone.strip() if phone else None
        if notes is not None:
            self.notes = notes
        self.updated_at = _utc_now()

    def archive(self) -> None:
        """Archive the contact."""
        self.status = ContactStatus.ARCHIVED
        self.updated_at = _utc_now()

    def restore(self) -> None:
        """Restore an archived contact."""
        self.status = ContactStatus.ACTIVE
        self.updated_at = _utc_now()

    def link_to_user(self, user_id: UUID) -> None:
        """Link this contact to a registered user.

        Args:
            user_id: The user's ID to link to.
        """
        self.linked_user_id = user_id
        self.share_status = ShareStatus.PENDING
        self.updated_at = _utc_now()

    def accept_share(self) -> None:
        """Accept sharing invitation (called when linked user accepts)."""
        if self.share_status != ShareStatus.PENDING:
            raise ValueError("No pending share invitation")
        self.share_status = ShareStatus.ACCEPTED
        self.updated_at = _utc_now()

    def decline_share(self) -> None:
        """Decline sharing invitation."""
        if self.share_status != ShareStatus.PENDING:
            raise ValueError("No pending share invitation")
        self.share_status = ShareStatus.DECLINED
        self.updated_at = _utc_now()

    @property
    def is_linked(self) -> bool:
        """Check if contact is linked to a registered user."""
        return self.linked_user_id is not None

    @property
    def is_shared(self) -> bool:
        """Check if records are actively shared with this contact."""
        return self.share_status == ShareStatus.ACCEPTED


@dataclass
class ContactGroup:
    """A group of contacts for expense splitting.

    Attributes:
        id: Unique identifier.
        tenant_id: Owner's tenant ID.
        name: Group name (e.g., "Roommates", "Trip to Paris").
        description: Optional description.
        member_ids: List of contact IDs who are members.
        created_at: When the group was created.
        updated_at: When the group was last updated.
    """

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    member_ids: list[UUID] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        description: str | None = None,
        member_ids: list[UUID] | None = None,
    ) -> ContactGroup:
        """Create a new contact group.

        Args:
            tenant_id: Owner's tenant ID.
            name: Group name.
            description: Optional description.
            member_ids: Initial member contact IDs.

        Returns:
            New ContactGroup instance.
        """
        if not name or not name.strip():
            raise ValueError("Group name is required")

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name.strip(),
            description=description,
            member_ids=member_ids or [],
        )

    def add_member(self, contact_id: UUID) -> None:
        """Add a member to the group."""
        if contact_id not in self.member_ids:
            self.member_ids.append(contact_id)
            self.updated_at = _utc_now()

    def remove_member(self, contact_id: UUID) -> None:
        """Remove a member from the group."""
        if contact_id in self.member_ids:
            self.member_ids.remove(contact_id)
            self.updated_at = _utc_now()

    @property
    def member_count(self) -> int:
        """Get the number of members."""
        return len(self.member_ids)


@dataclass
class PeerDebt:
    """A peer-to-peer debt (money lent or borrowed).

    Represents money that was lent to or borrowed from a contact.

    Attributes:
        id: Unique identifier.
        tenant_id: Owner's tenant ID.
        contact_id: The contact involved in this debt.
        direction: Whether owner lent or borrowed.
        amount: The original debt amount (always positive).
        currency_code: Currency of the debt.
        settled_amount: Amount that has been settled so far.
        description: Reason for the debt.
        debt_date: When the debt occurred.
        due_date: Optional due date for repayment.
        status: Current status of the debt.
        linked_transaction_id: Optional link to personal finance transaction.
        notes: Additional notes.
        created_at: When the record was created.
        updated_at: When the record was last updated.
    """

    id: UUID
    tenant_id: UUID
    contact_id: UUID
    direction: DebtDirection
    amount: Decimal
    currency_code: str
    settled_amount: Decimal = Decimal("0")
    description: str | None = None
    debt_date: date = field(default_factory=date.today)
    due_date: date | None = None
    status: DebtStatus = DebtStatus.ACTIVE
    linked_transaction_id: UUID | None = None
    notes: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """Validate debt after initialization."""
        if self.amount <= 0:
            raise ValueError("Debt amount must be positive")

    @classmethod
    def create_lent(
        cls,
        tenant_id: UUID,
        contact_id: UUID,
        amount: Decimal,
        currency_code: str,
        description: str | None = None,
        debt_date: date | None = None,
        due_date: date | None = None,
    ) -> PeerDebt:
        """Create a new debt where owner lent money to contact.

        Args:
            tenant_id: Owner's tenant ID.
            contact_id: Contact who received the money.
            amount: Amount lent.
            currency_code: Currency code.
            description: Reason for lending.
            debt_date: Date of the transaction.
            due_date: Optional due date.

        Returns:
            New PeerDebt instance.
        """
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            contact_id=contact_id,
            direction=DebtDirection.LENT,
            amount=amount,
            currency_code=currency_code.upper(),
            description=description,
            debt_date=debt_date or date.today(),
            due_date=due_date,
        )

    @classmethod
    def create_borrowed(
        cls,
        tenant_id: UUID,
        contact_id: UUID,
        amount: Decimal,
        currency_code: str,
        description: str | None = None,
        debt_date: date | None = None,
        due_date: date | None = None,
    ) -> PeerDebt:
        """Create a new debt where owner borrowed money from contact.

        Args:
            tenant_id: Owner's tenant ID.
            contact_id: Contact who gave the money.
            amount: Amount borrowed.
            currency_code: Currency code.
            description: Reason for borrowing.
            debt_date: Date of the transaction.
            due_date: Optional due date.

        Returns:
            New PeerDebt instance.
        """
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            contact_id=contact_id,
            direction=DebtDirection.BORROWED,
            amount=amount,
            currency_code=currency_code.upper(),
            description=description,
            debt_date=debt_date or date.today(),
            due_date=due_date,
        )

    @property
    def remaining_amount(self) -> Decimal:
        """Get the remaining unsettled amount."""
        return self.amount - self.settled_amount

    @property
    def is_fully_settled(self) -> bool:
        """Check if debt is fully settled."""
        return self.remaining_amount <= 0

    @property
    def signed_amount(self) -> Decimal:
        """Get signed amount from owner's perspective.

        Positive: Contact owes owner (LENT)
        Negative: Owner owes contact (BORROWED)
        """
        return self.remaining_amount * self.direction.sign

    def record_settlement(self, amount: Decimal) -> None:
        """Record a partial or full settlement.

        Args:
            amount: Amount being settled.

        Raises:
            ValueError: If amount exceeds remaining debt.
        """
        if amount <= 0:
            raise ValueError("Settlement amount must be positive")
        if amount > self.remaining_amount:
            raise ValueError("Settlement amount exceeds remaining debt")

        self.settled_amount += amount
        if self.is_fully_settled:
            self.status = DebtStatus.SETTLED
        self.updated_at = _utc_now()

    def cancel(self) -> None:
        """Cancel/forgive the debt."""
        self.status = DebtStatus.CANCELLED
        self.updated_at = _utc_now()


@dataclass
class ExpenseGroup:
    """A group for tracking shared expenses.

    This is the container for group expenses, separate from ContactGroup
    to allow more flexibility in expense tracking.

    Attributes:
        id: Unique identifier.
        tenant_id: Owner's tenant ID.
        name: Group name.
        description: Optional description.
        default_currency: Default currency for expenses in this group.
        member_contact_ids: Contact IDs of group members.
        include_self: Whether to include owner in splits.
        created_at: When the group was created.
        updated_at: When the group was last updated.
    """

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    default_currency: str = "USD"
    member_contact_ids: list[UUID] = field(default_factory=list)
    include_self: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        default_currency: str = "USD",
        description: str | None = None,
        member_contact_ids: list[UUID] | None = None,
        include_self: bool = True,
    ) -> ExpenseGroup:
        """Create a new expense group."""
        if not name or not name.strip():
            raise ValueError("Group name is required")

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name.strip(),
            description=description,
            default_currency=default_currency.upper(),
            member_contact_ids=member_contact_ids or [],
            include_self=include_self,
        )

    def add_member(self, contact_id: UUID) -> None:
        """Add a member to the group."""
        if contact_id not in self.member_contact_ids:
            self.member_contact_ids.append(contact_id)
            self.updated_at = _utc_now()

    def remove_member(self, contact_id: UUID) -> None:
        """Remove a member from the group."""
        if contact_id in self.member_contact_ids:
            self.member_contact_ids.remove(contact_id)
            self.updated_at = _utc_now()

    @property
    def total_members(self) -> int:
        """Get total number of members including owner if applicable."""
        count = len(self.member_contact_ids)
        if self.include_self:
            count += 1
        return count


@dataclass
class ExpenseSplit:
    """A single participant's share in a group expense.

    Attributes:
        id: Unique identifier.
        expense_id: The expense this split belongs to.
        contact_id: The contact this split is for (None for owner).
        is_owner: Whether this split is for the expense owner.
        share_amount: Amount this participant owes.
        settled_amount: Amount settled so far.
        status: Settlement status.
    """

    id: UUID
    expense_id: UUID
    contact_id: UUID | None  # None if is_owner is True
    is_owner: bool
    share_amount: Decimal
    settled_amount: Decimal = Decimal("0")
    status: SplitStatus = SplitStatus.PENDING

    @property
    def remaining_amount(self) -> Decimal:
        """Get remaining unsettled amount."""
        return self.share_amount - self.settled_amount

    def record_settlement(self, amount: Decimal) -> None:
        """Record a settlement for this split."""
        if amount <= 0:
            raise ValueError("Settlement amount must be positive")
        if amount > self.remaining_amount:
            raise ValueError("Settlement amount exceeds remaining")

        self.settled_amount += amount
        if self.remaining_amount <= 0:
            self.status = SplitStatus.SETTLED
        else:
            self.status = SplitStatus.PARTIAL


@dataclass
class GroupExpense:
    """A shared expense in a group.

    Attributes:
        id: Unique identifier.
        tenant_id: Owner's tenant ID.
        group_id: The expense group this belongs to.
        description: Description of the expense.
        total_amount: Total expense amount.
        currency_code: Currency of the expense.
        paid_by_contact_id: Contact who paid (None if owner paid).
        paid_by_owner: Whether the owner paid.
        split_method: How the expense is split.
        expense_date: When the expense occurred.
        splits: List of expense splits.
        status: Expense status.
        notes: Additional notes.
        created_at: When the expense was created.
        updated_at: When the expense was last updated.
    """

    id: UUID
    tenant_id: UUID
    group_id: UUID
    description: str
    total_amount: Decimal
    currency_code: str
    paid_by_contact_id: UUID | None = None
    paid_by_owner: bool = True
    split_method: SplitMethod = SplitMethod.EQUAL
    expense_date: date = field(default_factory=date.today)
    splits: list[ExpenseSplit] = field(default_factory=list)
    status: ExpenseStatus = ExpenseStatus.ACTIVE
    notes: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """Validate expense after initialization."""
        if self.total_amount <= 0:
            raise ValueError("Expense amount must be positive")
        if self.paid_by_owner and self.paid_by_contact_id is not None:
            raise ValueError("Cannot specify contact if owner paid")
        if not self.paid_by_owner and self.paid_by_contact_id is None:
            raise ValueError("Must specify contact if owner did not pay")

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        group_id: UUID,
        description: str,
        total_amount: Decimal,
        currency_code: str,
        paid_by_owner: bool = True,
        paid_by_contact_id: UUID | None = None,
        split_method: SplitMethod = SplitMethod.EQUAL,
        expense_date: date | None = None,
    ) -> GroupExpense:
        """Create a new group expense."""
        if not description or not description.strip():
            raise ValueError("Description is required")

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            group_id=group_id,
            description=description.strip(),
            total_amount=total_amount,
            currency_code=currency_code.upper(),
            paid_by_owner=paid_by_owner,
            paid_by_contact_id=paid_by_contact_id,
            split_method=split_method,
            expense_date=expense_date or date.today(),
        )

    def add_equal_splits(
        self,
        contact_ids: list[UUID],
        include_owner: bool = True,
    ) -> None:
        """Create equal splits for the expense.

        Args:
            contact_ids: Contact IDs to include in split.
            include_owner: Whether to include the owner in the split.
        """
        total_participants = len(contact_ids) + (1 if include_owner else 0)
        if total_participants == 0:
            raise ValueError("At least one participant required")

        share_amount = self.total_amount / total_participants

        self.splits = []

        # Add owner split if included
        if include_owner:
            self.splits.append(
                ExpenseSplit(
                    id=uuid4(),
                    expense_id=self.id,
                    contact_id=None,
                    is_owner=True,
                    share_amount=share_amount,
                )
            )

        # Add contact splits
        for contact_id in contact_ids:
            self.splits.append(
                ExpenseSplit(
                    id=uuid4(),
                    expense_id=self.id,
                    contact_id=contact_id,
                    is_owner=False,
                    share_amount=share_amount,
                )
            )

        self.updated_at = _utc_now()

    def add_exact_splits(
        self,
        splits: dict[UUID | None, Decimal],
    ) -> None:
        """Create splits with exact amounts.

        Args:
            splits: Dict mapping contact_id (or None for owner) to amount.

        Raises:
            ValueError: If splits don't add up to total.
        """
        total = sum(splits.values())
        if total != self.total_amount:
            raise ValueError(
                f"Splits ({total}) must equal total amount ({self.total_amount})"
            )

        self.splits = []
        for contact_id, amount in splits.items():
            self.splits.append(
                ExpenseSplit(
                    id=uuid4(),
                    expense_id=self.id,
                    contact_id=contact_id,
                    is_owner=contact_id is None,
                    share_amount=amount,
                )
            )

        self.updated_at = _utc_now()

    @property
    def is_fully_settled(self) -> bool:
        """Check if all splits are settled."""
        return all(s.status == SplitStatus.SETTLED for s in self.splits)

    def get_payer_split(self) -> ExpenseSplit | None:
        """Get the split for whoever paid."""
        if self.paid_by_owner:
            return next((s for s in self.splits if s.is_owner), None)
        return next(
            (s for s in self.splits if s.contact_id == self.paid_by_contact_id),
            None,
        )


@dataclass
class Settlement:
    """A settlement payment between owner and contact.

    Records a payment made to settle debts or expense splits.

    Attributes:
        id: Unique identifier.
        tenant_id: Owner's tenant ID.
        from_contact_id: Who paid (None if owner paid).
        to_contact_id: Who received (None if owner received).
        from_is_owner: Whether owner is the payer.
        to_is_owner: Whether owner is the receiver.
        amount: Settlement amount.
        currency_code: Currency of the settlement.
        method: Payment method.
        settlement_date: When the settlement was made.
        linked_debt_ids: Peer debts this settlement applies to.
        linked_split_ids: Expense splits this settlement applies to.
        notes: Additional notes.
        created_at: When the settlement was created.
    """

    id: UUID
    tenant_id: UUID
    from_contact_id: UUID | None
    to_contact_id: UUID | None
    from_is_owner: bool
    to_is_owner: bool
    amount: Decimal
    currency_code: str
    method: SettlementMethod = SettlementMethod.CASH
    settlement_date: date = field(default_factory=date.today)
    linked_debt_ids: list[UUID] = field(default_factory=list)
    linked_split_ids: list[UUID] = field(default_factory=list)
    notes: str | None = None
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """Validate settlement."""
        if self.amount <= 0:
            raise ValueError("Settlement amount must be positive")
        if self.from_is_owner and self.to_is_owner:
            raise ValueError("Owner cannot settle with themselves")
        if not self.from_is_owner and not self.to_is_owner:
            raise ValueError("At least one party must be the owner")
        if self.from_is_owner and self.from_contact_id is not None:
            raise ValueError("from_contact_id must be None if owner is payer")
        if self.to_is_owner and self.to_contact_id is not None:
            raise ValueError("to_contact_id must be None if owner is receiver")

    @classmethod
    def create_owner_pays(
        cls,
        tenant_id: UUID,
        to_contact_id: UUID,
        amount: Decimal,
        currency_code: str,
        method: SettlementMethod = SettlementMethod.CASH,
        settlement_date: date | None = None,
        notes: str | None = None,
    ) -> Settlement:
        """Create a settlement where owner pays the contact.

        Used when owner owes contact money (borrowed from them).
        """
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            from_contact_id=None,
            to_contact_id=to_contact_id,
            from_is_owner=True,
            to_is_owner=False,
            amount=amount,
            currency_code=currency_code.upper(),
            method=method,
            settlement_date=settlement_date or date.today(),
            notes=notes,
        )

    @classmethod
    def create_owner_receives(
        cls,
        tenant_id: UUID,
        from_contact_id: UUID,
        amount: Decimal,
        currency_code: str,
        method: SettlementMethod = SettlementMethod.CASH,
        settlement_date: date | None = None,
        notes: str | None = None,
    ) -> Settlement:
        """Create a settlement where owner receives from contact.

        Used when contact owes owner money (lent to them).
        """
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            from_contact_id=from_contact_id,
            to_contact_id=None,
            from_is_owner=False,
            to_is_owner=True,
            amount=amount,
            currency_code=currency_code.upper(),
            method=method,
            settlement_date=settlement_date or date.today(),
            notes=notes,
        )

    def link_debt(self, debt_id: UUID) -> None:
        """Link this settlement to a peer debt."""
        if debt_id not in self.linked_debt_ids:
            self.linked_debt_ids.append(debt_id)

    def link_split(self, split_id: UUID) -> None:
        """Link this settlement to an expense split."""
        if split_id not in self.linked_split_ids:
            self.linked_split_ids.append(split_id)
