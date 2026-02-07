"""Unit tests for social finance domain entities."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from modules.social.domain.entities import (
    Contact,
    ContactGroup,
    ExpenseGroup,
    ExpenseSplit,
    GroupExpense,
    PeerDebt,
    Settlement,
)
from modules.social.domain.enums import (
    ContactStatus,
    DebtDirection,
    DebtStatus,
    ExpenseStatus,
    ShareStatus,
    SplitMethod,
    SplitStatus,
)


class TestContact:
    """Tests for Contact entity."""

    def test_create_contact(self):
        """Test creating a contact with required fields."""
        tenant_id = uuid4()
        contact = Contact.create(
            tenant_id=tenant_id,
            name="John Doe",
            email="john@example.com",
        )

        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"
        assert contact.tenant_id == tenant_id
        assert contact.status == ContactStatus.ACTIVE
        assert contact.share_status == ShareStatus.NOT_SHARED

    def test_update_contact(self):
        """Test updating contact details."""
        contact = Contact.create(
            tenant_id=uuid4(),
            name="John Doe",
        )
        contact.update(name="Jane Doe")

        assert contact.name == "Jane Doe"

    def test_update_name_empty_raises(self):
        """Test that empty name raises error."""
        contact = Contact.create(
            tenant_id=uuid4(),
            name="John Doe",
        )

        with pytest.raises(ValueError, match="empty"):
            contact.update(name="")

    def test_archive_contact(self):
        """Test archiving a contact."""
        contact = Contact.create(
            tenant_id=uuid4(),
            name="John Doe",
        )
        contact.archive()

        assert contact.status == ContactStatus.ARCHIVED

    def test_restore_contact(self):
        """Test restoring an archived contact."""
        contact = Contact.create(
            tenant_id=uuid4(),
            name="John Doe",
        )
        contact.archive()
        contact.restore()

        assert contact.status == ContactStatus.ACTIVE

    def test_link_to_user(self):
        """Test linking contact to a user."""
        contact = Contact.create(
            tenant_id=uuid4(),
            name="John Doe",
        )
        user_id = uuid4()
        contact.link_to_user(user_id)

        assert contact.linked_user_id == user_id

    def test_is_linked(self):
        """Test is_linked property."""
        contact = Contact.create(
            tenant_id=uuid4(),
            name="John Doe",
        )

        assert contact.is_linked is False
        contact.link_to_user(uuid4())
        assert contact.is_linked is True


class TestContactGroup:
    """Tests for ContactGroup entity."""

    def test_create_group(self):
        """Test creating a contact group."""
        tenant_id = uuid4()
        group = ContactGroup.create(
            tenant_id=tenant_id,
            name="Friends",
            description="My friends",
        )

        assert group.name == "Friends"
        assert group.description == "My friends"
        assert group.member_count == 0

    def test_add_member(self):
        """Test adding a member to a group."""
        tenant_id = uuid4()
        group = ContactGroup.create(
            tenant_id=tenant_id,
            name="Friends",
        )
        contact_id = uuid4()

        group.add_member(contact_id)

        assert contact_id in group.member_ids
        assert group.member_count == 1

    def test_add_duplicate_member(self):
        """Test that adding duplicate member is idempotent."""
        tenant_id = uuid4()
        group = ContactGroup.create(
            tenant_id=tenant_id,
            name="Friends",
        )
        contact_id = uuid4()

        group.add_member(contact_id)
        group.add_member(contact_id)

        assert group.member_count == 1

    def test_remove_member(self):
        """Test removing a member from a group."""
        tenant_id = uuid4()
        group = ContactGroup.create(
            tenant_id=tenant_id,
            name="Friends",
        )
        contact_id = uuid4()

        group.add_member(contact_id)
        group.remove_member(contact_id)

        assert contact_id not in group.member_ids
        assert group.member_count == 0


class TestPeerDebt:
    """Tests for PeerDebt entity."""

    def test_create_lent_debt(self):
        """Test creating a lent debt."""
        tenant_id = uuid4()
        contact_id = uuid4()
        debt = PeerDebt.create_lent(
            tenant_id=tenant_id,
            contact_id=contact_id,
            amount=Decimal("100.00"),
            currency_code="USD",
            description="Lunch money",
        )

        assert debt.direction == DebtDirection.LENT
        assert debt.amount == Decimal("100.00")
        assert debt.remaining_amount == Decimal("100.00")
        assert debt.status == DebtStatus.ACTIVE

    def test_create_borrowed_debt(self):
        """Test creating a borrowed debt."""
        tenant_id = uuid4()
        contact_id = uuid4()
        debt = PeerDebt.create_borrowed(
            tenant_id=tenant_id,
            contact_id=contact_id,
            amount=Decimal("50.00"),
            currency_code="USD",
        )

        assert debt.direction == DebtDirection.BORROWED
        assert debt.amount == Decimal("50.00")

    def test_settle_partial(self):
        """Test partial settlement of debt."""
        debt = PeerDebt.create_lent(
            tenant_id=uuid4(),
            contact_id=uuid4(),
            amount=Decimal("100.00"),
            currency_code="USD",
        )

        debt.record_settlement(Decimal("30.00"))

        assert debt.settled_amount == Decimal("30.00")
        assert debt.remaining_amount == Decimal("70.00")
        assert debt.status == DebtStatus.ACTIVE

    def test_settle_fully(self):
        """Test full settlement of debt."""
        debt = PeerDebt.create_lent(
            tenant_id=uuid4(),
            contact_id=uuid4(),
            amount=Decimal("100.00"),
            currency_code="USD",
        )

        debt.record_settlement(Decimal("100.00"))

        assert debt.settled_amount == Decimal("100.00")
        assert debt.remaining_amount == Decimal("0.00")
        assert debt.status == DebtStatus.SETTLED

    def test_settle_over_amount_raises(self):
        """Test that settling more than remaining raises error."""
        debt = PeerDebt.create_lent(
            tenant_id=uuid4(),
            contact_id=uuid4(),
            amount=Decimal("100.00"),
            currency_code="USD",
        )

        with pytest.raises(ValueError, match="exceeds"):
            debt.record_settlement(Decimal("150.00"))

    def test_cancel_debt(self):
        """Test canceling a debt."""
        debt = PeerDebt.create_lent(
            tenant_id=uuid4(),
            contact_id=uuid4(),
            amount=Decimal("100.00"),
            currency_code="USD",
        )

        debt.cancel()

        assert debt.status == DebtStatus.CANCELLED


class TestExpenseGroup:
    """Tests for ExpenseGroup entity."""

    def test_create_expense_group(self):
        """Test creating an expense group."""
        tenant_id = uuid4()
        group = ExpenseGroup.create(
            tenant_id=tenant_id,
            name="Trip to Paris",
            default_currency="EUR",
            include_self=True,
        )

        assert group.name == "Trip to Paris"
        assert group.default_currency == "EUR"
        assert group.include_self is True
        assert group.total_members == 1  # Owner included

    def test_add_member_to_expense_group(self):
        """Test adding a member to expense group."""
        tenant_id = uuid4()
        group = ExpenseGroup.create(
            tenant_id=tenant_id,
            name="Trip",
        )
        contact_id = uuid4()

        group.add_member(contact_id)

        assert contact_id in group.member_contact_ids
        assert group.total_members == 2  # Owner + 1 contact


class TestGroupExpense:
    """Tests for GroupExpense entity."""

    def test_create_expense(self):
        """Test creating a group expense."""
        tenant_id = uuid4()
        group_id = uuid4()
        expense = GroupExpense.create(
            tenant_id=tenant_id,
            group_id=group_id,
            description="Dinner",
            total_amount=Decimal("120.00"),
            currency_code="USD",
            paid_by_owner=True,
            split_method=SplitMethod.EQUAL,
        )

        assert expense.description == "Dinner"
        assert expense.total_amount == Decimal("120.00")
        assert expense.status == ExpenseStatus.ACTIVE

    def test_add_equal_splits(self):
        """Test adding equal splits."""
        tenant_id = uuid4()
        expense = GroupExpense.create(
            tenant_id=tenant_id,
            group_id=uuid4(),
            description="Dinner",
            total_amount=Decimal("90.00"),
            currency_code="USD",
            paid_by_owner=True,
        )

        contact_ids = [uuid4(), uuid4()]
        expense.add_equal_splits(
            contact_ids=contact_ids,
            include_owner=True,
        )

        assert len(expense.splits) == 3  # 2 contacts + owner
        for split in expense.splits:
            assert split.share_amount == Decimal("30.00")

    def test_add_exact_splits(self):
        """Test setting exact splits."""
        tenant_id = uuid4()
        contact1_id = uuid4()
        contact2_id = uuid4()
        expense = GroupExpense.create(
            tenant_id=tenant_id,
            group_id=uuid4(),
            description="Dinner",
            total_amount=Decimal("100.00"),
            currency_code="USD",
            paid_by_owner=True,
            split_method=SplitMethod.EXACT,
        )

        exact_splits = {
            None: Decimal("50.00"),  # Owner
            contact1_id: Decimal("30.00"),
            contact2_id: Decimal("20.00"),
        }
        expense.add_exact_splits(exact_splits)

        assert len(expense.splits) == 3
        owner_split = next(s for s in expense.splits if s.is_owner)
        assert owner_split.share_amount == Decimal("50.00")

    def test_add_exact_splits_wrong_total_raises(self):
        """Test that wrong total raises error."""
        expense = GroupExpense.create(
            tenant_id=uuid4(),
            group_id=uuid4(),
            description="Dinner",
            total_amount=Decimal("100.00"),
            currency_code="USD",
            paid_by_owner=True,
            split_method=SplitMethod.EXACT,
        )

        with pytest.raises(ValueError, match="must equal"):
            expense.add_exact_splits({
                None: Decimal("50.00"),
            })


class TestSettlement:
    """Tests for Settlement entity."""

    def test_create_settlement_owner_pays(self):
        """Test creating a settlement where owner pays."""
        tenant_id = uuid4()
        contact_id = uuid4()
        settlement = Settlement.create_owner_pays(
            tenant_id=tenant_id,
            to_contact_id=contact_id,
            amount=Decimal("50.00"),
            currency_code="USD",
        )

        assert settlement.from_is_owner is True
        assert settlement.to_is_owner is False
        assert settlement.to_contact_id == contact_id
        assert settlement.amount == Decimal("50.00")

    def test_create_settlement_owner_receives(self):
        """Test creating a settlement where owner receives."""
        tenant_id = uuid4()
        contact_id = uuid4()
        settlement = Settlement.create_owner_receives(
            tenant_id=tenant_id,
            from_contact_id=contact_id,
            amount=Decimal("75.00"),
            currency_code="USD",
        )

        assert settlement.from_is_owner is False
        assert settlement.to_is_owner is True
        assert settlement.from_contact_id == contact_id

    def test_link_to_debt(self):
        """Test linking settlement to a debt."""
        settlement = Settlement.create_owner_receives(
            tenant_id=uuid4(),
            from_contact_id=uuid4(),
            amount=Decimal("50.00"),
            currency_code="USD",
        )
        debt_id = uuid4()

        settlement.link_debt(debt_id)

        assert debt_id in settlement.linked_debt_ids
