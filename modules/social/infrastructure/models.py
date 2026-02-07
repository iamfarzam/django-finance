"""Django ORM models for the social finance module."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from modules.social.domain.enums import (
    ContactStatus,
    DebtDirection,
    DebtStatus,
    ExpenseStatus,
    ShareStatus,
    SplitMethod,
    SplitStatus,
)


class Contact(models.Model):
    """Contact model for storing friends/people in finance tracking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value) for s in ContactStatus],
        default=ContactStatus.ACTIVE.value,
    )

    # Link to registered user (optional)
    linked_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_contacts",
    )

    share_status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value) for s in ShareStatus],
        default=ShareStatus.NOT_SHARED.value,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_contact"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "email"]),
            models.Index(fields=["linked_user"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "email"],
                name="unique_contact_email_per_tenant",
                condition=models.Q(email__isnull=False),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.tenant_id})"


class ContactGroup(models.Model):
    """Contact group model for organizing contacts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    members = models.ManyToManyField(
        Contact,
        related_name="contact_groups",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_contact_group"
        indexes = [
            models.Index(fields=["tenant_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.member_count} members)"

    @property
    def member_count(self) -> int:
        return self.members.count()


class PeerDebt(models.Model):
    """Peer debt model for tracking money lent/borrowed."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="debts",
    )

    direction = models.CharField(
        max_length=10,
        choices=[(d.value, d.value) for d in DebtDirection],
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency_code = models.CharField(max_length=3, default="USD")
    settled_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )

    description = models.TextField(blank=True, null=True)
    debt_date = models.DateField()
    due_date = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value) for s in DebtStatus],
        default=DebtStatus.ACTIVE.value,
    )

    # Optional link to a transaction
    linked_transaction_id = models.UUIDField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_peer_debt"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["tenant_id", "contact"]),
            models.Index(fields=["debt_date"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.direction}: {self.amount} {self.currency_code} with {self.contact.name}"

    @property
    def remaining_amount(self) -> Decimal:
        return self.amount - self.settled_amount


class ExpenseGroup(models.Model):
    """Expense group model for group expense splitting."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    default_currency = models.CharField(max_length=3, default="USD")

    member_contacts = models.ManyToManyField(
        Contact,
        related_name="expense_groups",
        blank=True,
    )

    include_self = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_expense_group"
        indexes = [
            models.Index(fields=["tenant_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.total_members} members)"

    @property
    def total_members(self) -> int:
        count = self.member_contacts.count()
        if self.include_self:
            count += 1
        return count


class GroupExpense(models.Model):
    """Group expense model for shared expenses."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    group = models.ForeignKey(
        ExpenseGroup,
        on_delete=models.CASCADE,
        related_name="expenses",
    )

    description = models.CharField(max_length=500)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency_code = models.CharField(max_length=3, default="USD")

    # Who paid
    paid_by_owner = models.BooleanField(default=True)
    paid_by_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paid_expenses",
    )

    split_method = models.CharField(
        max_length=20,
        choices=[(m.value, m.value) for m in SplitMethod],
        default=SplitMethod.EQUAL.value,
    )

    expense_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value) for s in ExpenseStatus],
        default=ExpenseStatus.ACTIVE.value,
    )

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_group_expense"
        indexes = [
            models.Index(fields=["tenant_id", "status"]),
            models.Index(fields=["group"]),
            models.Index(fields=["expense_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.description}: {self.total_amount} {self.currency_code}"


class ExpenseSplit(models.Model):
    """Expense split model for individual shares."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    expense = models.ForeignKey(
        GroupExpense,
        on_delete=models.CASCADE,
        related_name="splits",
    )

    # Contact or owner
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="expense_splits",
    )
    is_owner = models.BooleanField(default=False)

    share_amount = models.DecimalField(max_digits=15, decimal_places=2)
    settled_amount = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )

    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.value) for s in SplitStatus],
        default=SplitStatus.PENDING.value,
    )

    class Meta:
        db_table = "social_expense_split"
        indexes = [
            models.Index(fields=["expense"]),
            models.Index(fields=["contact"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(contact__isnull=False) | models.Q(is_owner=True),
                name="split_must_have_contact_or_be_owner",
            ),
        ]

    def __str__(self) -> str:
        participant = "Owner" if self.is_owner else str(self.contact)
        return f"{participant}: {self.share_amount}"

    @property
    def remaining_amount(self) -> Decimal:
        return self.share_amount - self.settled_amount


class Settlement(models.Model):
    """Settlement model for recording payments."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)

    # From party
    from_is_owner = models.BooleanField(default=False)
    from_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="settlements_from",
    )

    # To party
    to_is_owner = models.BooleanField(default=False)
    to_contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="settlements_to",
    )

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency_code = models.CharField(max_length=3, default="USD")
    method = models.CharField(max_length=50, default="cash")
    settlement_date = models.DateField()

    # Links to what this settlement covers
    linked_debts = models.ManyToManyField(
        PeerDebt,
        related_name="settlements",
        blank=True,
    )
    linked_splits = models.ManyToManyField(
        ExpenseSplit,
        related_name="settlements",
        blank=True,
    )

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "social_settlement"
        indexes = [
            models.Index(fields=["tenant_id"]),
            models.Index(fields=["settlement_date"]),
            models.Index(fields=["from_contact"]),
            models.Index(fields=["to_contact"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(from_is_owner=True, from_contact__isnull=True)
                    | models.Q(from_is_owner=False, from_contact__isnull=False)
                ),
                name="settlement_from_valid",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(to_is_owner=True, to_contact__isnull=True)
                    | models.Q(to_is_owner=False, to_contact__isnull=False)
                ),
                name="settlement_to_valid",
            ),
        ]

    def __str__(self) -> str:
        from_party = "Owner" if self.from_is_owner else str(self.from_contact)
        to_party = "Owner" if self.to_is_owner else str(self.to_contact)
        return f"{from_party} -> {to_party}: {self.amount} {self.currency_code}"
