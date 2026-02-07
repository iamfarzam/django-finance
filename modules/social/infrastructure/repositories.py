"""Repository implementations for the social finance module."""

from __future__ import annotations

from datetime import timezone
from typing import TYPE_CHECKING
from uuid import UUID

from modules.social.application.interfaces import (
    ContactGroupRepository,
    ContactRepository,
    ExpenseGroupRepository,
    GroupExpenseRepository,
    PeerDebtRepository,
    SettlementRepository,
)
from modules.social.domain.entities import (
    Contact as ContactEntity,
    ContactGroup as ContactGroupEntity,
    ExpenseGroup as ExpenseGroupEntity,
    ExpenseSplit as ExpenseSplitEntity,
    GroupExpense as GroupExpenseEntity,
    PeerDebt as PeerDebtEntity,
    Settlement as SettlementEntity,
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
from modules.social.infrastructure.models import (
    Contact,
    ContactGroup,
    ExpenseGroup,
    ExpenseSplit,
    GroupExpense,
    PeerDebt,
    Settlement,
)


class DjangoContactRepository(ContactRepository):
    """Django ORM implementation of ContactRepository."""

    def get_by_id(self, contact_id: UUID, tenant_id: UUID) -> ContactEntity | None:
        """Get a contact by ID."""
        try:
            model = Contact.objects.get(id=contact_id, tenant_id=tenant_id)
            return self._to_entity(model)
        except Contact.DoesNotExist:
            return None

    def get_all(self, tenant_id: UUID) -> list[ContactEntity]:
        """Get all contacts for a tenant."""
        models = Contact.objects.filter(tenant_id=tenant_id).order_by("-created_at")
        return [self._to_entity(m) for m in models]

    def get_by_email(self, email: str, tenant_id: UUID) -> ContactEntity | None:
        """Get a contact by email."""
        try:
            model = Contact.objects.get(email=email, tenant_id=tenant_id)
            return self._to_entity(model)
        except Contact.DoesNotExist:
            return None

    def get_by_linked_user(self, user_id: UUID) -> list[ContactEntity]:
        """Get all contacts linked to a user."""
        models = Contact.objects.filter(linked_user_id=user_id)
        return [self._to_entity(m) for m in models]

    def save(self, contact: ContactEntity) -> ContactEntity:
        """Save a contact."""
        model, _ = Contact.objects.update_or_create(
            id=contact.id,
            defaults={
                "tenant_id": contact.tenant_id,
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "avatar_url": contact.avatar_url,
                "notes": contact.notes,
                "status": contact.status.value,
                "linked_user_id": contact.linked_user_id,
                "share_status": contact.share_status.value,
            },
        )
        return self._to_entity(model)

    def delete(self, contact_id: UUID, tenant_id: UUID) -> bool:
        """Delete a contact."""
        deleted, _ = Contact.objects.filter(
            id=contact_id, tenant_id=tenant_id
        ).delete()
        return deleted > 0

    def _to_entity(self, model: Contact) -> ContactEntity:
        """Convert model to entity."""
        return ContactEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            email=model.email,
            phone=model.phone,
            avatar_url=model.avatar_url,
            notes=model.notes,
            status=ContactStatus(model.status),
            linked_user_id=model.linked_user_id,
            share_status=ShareStatus(model.share_status),
            created_at=model.created_at.replace(tzinfo=timezone.utc)
            if model.created_at.tzinfo is None
            else model.created_at,
            updated_at=model.updated_at.replace(tzinfo=timezone.utc)
            if model.updated_at.tzinfo is None
            else model.updated_at,
        )


class DjangoContactGroupRepository(ContactGroupRepository):
    """Django ORM implementation of ContactGroupRepository."""

    def get_by_id(self, group_id: UUID, tenant_id: UUID) -> ContactGroupEntity | None:
        """Get a group by ID."""
        try:
            model = ContactGroup.objects.prefetch_related("members").get(
                id=group_id, tenant_id=tenant_id
            )
            return self._to_entity(model)
        except ContactGroup.DoesNotExist:
            return None

    def get_all(self, tenant_id: UUID) -> list[ContactGroupEntity]:
        """Get all groups for a tenant."""
        models = ContactGroup.objects.filter(tenant_id=tenant_id).prefetch_related(
            "members"
        )
        return [self._to_entity(m) for m in models]

    def get_by_member(
        self, contact_id: UUID, tenant_id: UUID
    ) -> list[ContactGroupEntity]:
        """Get all groups a contact is a member of."""
        models = ContactGroup.objects.filter(
            tenant_id=tenant_id, members__id=contact_id
        ).prefetch_related("members")
        return [self._to_entity(m) for m in models]

    def save(self, group: ContactGroupEntity) -> ContactGroupEntity:
        """Save a group."""
        model, created = ContactGroup.objects.update_or_create(
            id=group.id,
            defaults={
                "tenant_id": group.tenant_id,
                "name": group.name,
                "description": group.description,
            },
        )

        # Update members
        model.members.set(Contact.objects.filter(id__in=group.member_ids))

        return self._to_entity(model)

    def delete(self, group_id: UUID, tenant_id: UUID) -> bool:
        """Delete a group."""
        deleted, _ = ContactGroup.objects.filter(
            id=group_id, tenant_id=tenant_id
        ).delete()
        return deleted > 0

    def _to_entity(self, model: ContactGroup) -> ContactGroupEntity:
        """Convert model to entity."""
        entity = ContactGroupEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            description=model.description,
            created_at=model.created_at.replace(tzinfo=timezone.utc)
            if model.created_at.tzinfo is None
            else model.created_at,
            updated_at=model.updated_at.replace(tzinfo=timezone.utc)
            if model.updated_at.tzinfo is None
            else model.updated_at,
        )
        entity._member_ids = set(model.members.values_list("id", flat=True))
        return entity


class DjangoPeerDebtRepository(PeerDebtRepository):
    """Django ORM implementation of PeerDebtRepository."""

    def get_by_id(self, debt_id: UUID, tenant_id: UUID) -> PeerDebtEntity | None:
        """Get a debt by ID."""
        try:
            model = PeerDebt.objects.get(id=debt_id, tenant_id=tenant_id)
            return self._to_entity(model)
        except PeerDebt.DoesNotExist:
            return None

    def get_all(self, tenant_id: UUID) -> list[PeerDebtEntity]:
        """Get all debts for a tenant."""
        models = PeerDebt.objects.filter(tenant_id=tenant_id).order_by("-debt_date")
        return [self._to_entity(m) for m in models]

    def get_by_contact(
        self, contact_id: UUID, tenant_id: UUID
    ) -> list[PeerDebtEntity]:
        """Get all debts with a specific contact."""
        models = PeerDebt.objects.filter(
            tenant_id=tenant_id, contact_id=contact_id
        ).order_by("-debt_date")
        return [self._to_entity(m) for m in models]

    def get_active(self, tenant_id: UUID) -> list[PeerDebtEntity]:
        """Get all active (unsettled) debts."""
        models = PeerDebt.objects.filter(
            tenant_id=tenant_id, status=DebtStatus.ACTIVE.value
        ).order_by("-debt_date")
        return [self._to_entity(m) for m in models]

    def save(self, debt: PeerDebtEntity) -> PeerDebtEntity:
        """Save a debt."""
        model, _ = PeerDebt.objects.update_or_create(
            id=debt.id,
            defaults={
                "tenant_id": debt.tenant_id,
                "contact_id": debt.contact_id,
                "direction": debt.direction.value,
                "amount": debt.amount,
                "currency_code": debt.currency_code,
                "settled_amount": debt.settled_amount,
                "description": debt.description,
                "debt_date": debt.debt_date,
                "due_date": debt.due_date,
                "status": debt.status.value,
                "linked_transaction_id": debt.linked_transaction_id,
                "notes": debt.notes,
            },
        )
        return self._to_entity(model)

    def delete(self, debt_id: UUID, tenant_id: UUID) -> bool:
        """Delete a debt."""
        deleted, _ = PeerDebt.objects.filter(id=debt_id, tenant_id=tenant_id).delete()
        return deleted > 0

    def _to_entity(self, model: PeerDebt) -> PeerDebtEntity:
        """Convert model to entity."""
        return PeerDebtEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            contact_id=model.contact_id,
            direction=DebtDirection(model.direction),
            amount=model.amount,
            currency_code=model.currency_code,
            settled_amount=model.settled_amount,
            description=model.description,
            debt_date=model.debt_date,
            due_date=model.due_date,
            status=DebtStatus(model.status),
            linked_transaction_id=model.linked_transaction_id,
            notes=model.notes,
            created_at=model.created_at.replace(tzinfo=timezone.utc)
            if model.created_at.tzinfo is None
            else model.created_at,
            updated_at=model.updated_at.replace(tzinfo=timezone.utc)
            if model.updated_at.tzinfo is None
            else model.updated_at,
        )


class DjangoExpenseGroupRepository(ExpenseGroupRepository):
    """Django ORM implementation of ExpenseGroupRepository."""

    def get_by_id(
        self, group_id: UUID, tenant_id: UUID
    ) -> ExpenseGroupEntity | None:
        """Get an expense group by ID."""
        try:
            model = ExpenseGroup.objects.prefetch_related("member_contacts").get(
                id=group_id, tenant_id=tenant_id
            )
            return self._to_entity(model)
        except ExpenseGroup.DoesNotExist:
            return None

    def get_all(self, tenant_id: UUID) -> list[ExpenseGroupEntity]:
        """Get all expense groups for a tenant."""
        models = ExpenseGroup.objects.filter(tenant_id=tenant_id).prefetch_related(
            "member_contacts"
        )
        return [self._to_entity(m) for m in models]

    def save(self, group: ExpenseGroupEntity) -> ExpenseGroupEntity:
        """Save an expense group."""
        model, _ = ExpenseGroup.objects.update_or_create(
            id=group.id,
            defaults={
                "tenant_id": group.tenant_id,
                "name": group.name,
                "description": group.description,
                "default_currency": group.default_currency,
                "include_self": group.include_self,
            },
        )

        # Update members
        model.member_contacts.set(
            Contact.objects.filter(id__in=group.member_contact_ids)
        )

        return self._to_entity(model)

    def delete(self, group_id: UUID, tenant_id: UUID) -> bool:
        """Delete an expense group."""
        deleted, _ = ExpenseGroup.objects.filter(
            id=group_id, tenant_id=tenant_id
        ).delete()
        return deleted > 0

    def _to_entity(self, model: ExpenseGroup) -> ExpenseGroupEntity:
        """Convert model to entity."""
        entity = ExpenseGroupEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            description=model.description,
            default_currency=model.default_currency,
            include_self=model.include_self,
            created_at=model.created_at.replace(tzinfo=timezone.utc)
            if model.created_at.tzinfo is None
            else model.created_at,
            updated_at=model.updated_at.replace(tzinfo=timezone.utc)
            if model.updated_at.tzinfo is None
            else model.updated_at,
        )
        entity._member_contact_ids = set(
            model.member_contacts.values_list("id", flat=True)
        )
        return entity


class DjangoGroupExpenseRepository(GroupExpenseRepository):
    """Django ORM implementation of GroupExpenseRepository."""

    def get_by_id(
        self, expense_id: UUID, tenant_id: UUID
    ) -> GroupExpenseEntity | None:
        """Get an expense by ID."""
        try:
            model = GroupExpense.objects.prefetch_related("splits").get(
                id=expense_id, tenant_id=tenant_id
            )
            return self._to_entity(model)
        except GroupExpense.DoesNotExist:
            return None

    def get_by_group(
        self, group_id: UUID, tenant_id: UUID
    ) -> list[GroupExpenseEntity]:
        """Get all expenses in a group."""
        models = GroupExpense.objects.filter(
            tenant_id=tenant_id, group_id=group_id
        ).prefetch_related("splits").order_by("-expense_date")
        return [self._to_entity(m) for m in models]

    def get_all(self, tenant_id: UUID) -> list[GroupExpenseEntity]:
        """Get all expenses for a tenant."""
        models = GroupExpense.objects.filter(tenant_id=tenant_id).prefetch_related(
            "splits"
        ).order_by("-expense_date")
        return [self._to_entity(m) for m in models]

    def save(self, expense: GroupExpenseEntity) -> GroupExpenseEntity:
        """Save an expense with its splits."""
        model, _ = GroupExpense.objects.update_or_create(
            id=expense.id,
            defaults={
                "tenant_id": expense.tenant_id,
                "group_id": expense.group_id,
                "description": expense.description,
                "total_amount": expense.total_amount,
                "currency_code": expense.currency_code,
                "paid_by_owner": expense.paid_by_owner,
                "paid_by_contact_id": expense.paid_by_contact_id,
                "split_method": expense.split_method.value,
                "expense_date": expense.expense_date,
                "status": expense.status.value,
                "notes": expense.notes,
            },
        )

        # Save splits
        existing_split_ids = set(
            ExpenseSplit.objects.filter(expense=model).values_list("id", flat=True)
        )
        new_split_ids = set()

        for split in expense.splits:
            ExpenseSplit.objects.update_or_create(
                id=split.id,
                defaults={
                    "expense": model,
                    "contact_id": split.contact_id,
                    "is_owner": split.is_owner,
                    "share_amount": split.share_amount,
                    "settled_amount": split.settled_amount,
                    "status": split.status.value,
                },
            )
            new_split_ids.add(split.id)

        # Delete removed splits
        to_delete = existing_split_ids - new_split_ids
        if to_delete:
            ExpenseSplit.objects.filter(id__in=to_delete).delete()

        # Refresh model with splits
        model.refresh_from_db()
        return self._to_entity(model)

    def delete(self, expense_id: UUID, tenant_id: UUID) -> bool:
        """Delete an expense."""
        deleted, _ = GroupExpense.objects.filter(
            id=expense_id, tenant_id=tenant_id
        ).delete()
        return deleted > 0

    def _to_entity(self, model: GroupExpense) -> GroupExpenseEntity:
        """Convert model to entity."""
        splits = [
            ExpenseSplitEntity(
                id=s.id,
                expense_id=s.expense_id,
                contact_id=s.contact_id,
                is_owner=s.is_owner,
                share_amount=s.share_amount,
                settled_amount=s.settled_amount,
                status=SplitStatus(s.status),
            )
            for s in model.splits.all()
        ]

        return GroupExpenseEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            group_id=model.group_id,
            description=model.description,
            total_amount=model.total_amount,
            currency_code=model.currency_code,
            paid_by_owner=model.paid_by_owner,
            paid_by_contact_id=model.paid_by_contact_id,
            split_method=SplitMethod(model.split_method),
            expense_date=model.expense_date,
            status=ExpenseStatus(model.status),
            notes=model.notes,
            splits=splits,
            created_at=model.created_at.replace(tzinfo=timezone.utc)
            if model.created_at.tzinfo is None
            else model.created_at,
            updated_at=model.updated_at.replace(tzinfo=timezone.utc)
            if model.updated_at.tzinfo is None
            else model.updated_at,
        )


class DjangoSettlementRepository(SettlementRepository):
    """Django ORM implementation of SettlementRepository."""

    def get_by_id(
        self, settlement_id: UUID, tenant_id: UUID
    ) -> SettlementEntity | None:
        """Get a settlement by ID."""
        try:
            model = Settlement.objects.prefetch_related(
                "linked_debts", "linked_splits"
            ).get(id=settlement_id, tenant_id=tenant_id)
            return self._to_entity(model)
        except Settlement.DoesNotExist:
            return None

    def get_all(self, tenant_id: UUID) -> list[SettlementEntity]:
        """Get all settlements for a tenant."""
        models = Settlement.objects.filter(tenant_id=tenant_id).prefetch_related(
            "linked_debts", "linked_splits"
        ).order_by("-settlement_date")
        return [self._to_entity(m) for m in models]

    def get_by_contact(
        self, contact_id: UUID, tenant_id: UUID
    ) -> list[SettlementEntity]:
        """Get all settlements with a specific contact."""
        from django.db.models import Q

        models = Settlement.objects.filter(
            Q(from_contact_id=contact_id) | Q(to_contact_id=contact_id),
            tenant_id=tenant_id,
        ).prefetch_related("linked_debts", "linked_splits").order_by("-settlement_date")
        return [self._to_entity(m) for m in models]

    def get_by_debt(self, debt_id: UUID) -> list[SettlementEntity]:
        """Get all settlements linked to a debt."""
        models = Settlement.objects.filter(
            linked_debts__id=debt_id
        ).prefetch_related("linked_debts", "linked_splits")
        return [self._to_entity(m) for m in models]

    def save(self, settlement: SettlementEntity) -> SettlementEntity:
        """Save a settlement."""
        model, _ = Settlement.objects.update_or_create(
            id=settlement.id,
            defaults={
                "tenant_id": settlement.tenant_id,
                "from_is_owner": settlement.from_is_owner,
                "from_contact_id": settlement.from_contact_id,
                "to_is_owner": settlement.to_is_owner,
                "to_contact_id": settlement.to_contact_id,
                "amount": settlement.amount,
                "currency_code": settlement.currency_code,
                "method": settlement.method,
                "settlement_date": settlement.settlement_date,
                "notes": settlement.notes,
            },
        )

        # Update linked debts and splits
        model.linked_debts.set(
            PeerDebt.objects.filter(id__in=settlement.linked_debt_ids)
        )
        model.linked_splits.set(
            ExpenseSplit.objects.filter(id__in=settlement.linked_split_ids)
        )

        return self._to_entity(model)

    def delete(self, settlement_id: UUID, tenant_id: UUID) -> bool:
        """Delete a settlement."""
        deleted, _ = Settlement.objects.filter(
            id=settlement_id, tenant_id=tenant_id
        ).delete()
        return deleted > 0

    def _to_entity(self, model: Settlement) -> SettlementEntity:
        """Convert model to entity."""
        entity = SettlementEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            from_is_owner=model.from_is_owner,
            from_contact_id=model.from_contact_id,
            to_is_owner=model.to_is_owner,
            to_contact_id=model.to_contact_id,
            amount=model.amount,
            currency_code=model.currency_code,
            method=model.method,
            settlement_date=model.settlement_date,
            notes=model.notes,
            created_at=model.created_at.replace(tzinfo=timezone.utc)
            if model.created_at.tzinfo is None
            else model.created_at,
        )
        entity._linked_debt_ids = set(
            model.linked_debts.values_list("id", flat=True)
        )
        entity._linked_split_ids = set(
            model.linked_splits.values_list("id", flat=True)
        )
        return entity
