"""Use cases for the social finance module.

These use cases orchestrate domain logic and repository operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from modules.social.application.dto import (
    ContactBalanceDTO,
    ContactDTO,
    ContactGroupDTO,
    CreateContactCommand,
    CreateContactGroupCommand,
    CreateExpenseGroupCommand,
    CreateGroupExpenseCommand,
    CreatePeerDebtCommand,
    CreateSettlementCommand,
    ExpenseGroupDTO,
    ExpenseSplitDTO,
    GroupBalanceDTO,
    GroupBalanceEntryDTO,
    GroupExpenseDTO,
    PeerDebtDTO,
    SettlementDTO,
    SettlementSuggestionDTO,
    SettleDebtCommand,
    UpdateContactCommand,
)
from modules.social.application.interfaces import (
    ContactGroupRepository,
    ContactRepository,
    ExpenseGroupRepository,
    GroupExpenseRepository,
    PeerDebtRepository,
    SettlementRepository,
)
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
from modules.social.domain.events import (
    BalanceUpdated,
    ContactArchived,
    ContactCreated,
    ContactUpdated,
    ExpenseGroupCreated,
    ExpenseGroupMemberAdded,
    GroupExpenseCreated,
    PeerDebtCreated,
    PeerDebtSettled,
    SettlementCreated,
)
from modules.social.domain.exceptions import (
    ContactNotFoundError,
    DebtAlreadySettledError,
    DebtNotFoundError,
    ExpenseGroupNotFoundError,
    GroupExpenseNotFoundError,
    InsufficientSettlementAmountError,
    InvalidSplitTotalError,
    SettlementNotFoundError,
)
from modules.social.domain.services import (
    DebtCalculator,
    GroupBalanceCalculator,
    SettlementSuggestionService,
    SimplifyDebtsService,
)

if TYPE_CHECKING:
    from contracts.events.base import EventBus


# =============================================================================
# Contact Use Cases
# =============================================================================


@dataclass
class ContactUseCases:
    """Use cases for contact management."""

    contact_repo: ContactRepository
    event_bus: "EventBus | None" = None

    def create_contact(self, command: CreateContactCommand) -> ContactDTO:
        """Create a new contact."""
        contact = Contact.create(
            tenant_id=command.tenant_id,
            name=command.name,
            email=command.email,
            phone=command.phone,
            notes=command.notes,
        )
        saved = self.contact_repo.save(contact)

        if self.event_bus:
            self.event_bus.publish(
                ContactCreated(
                    contact_id=saved.id,
                    tenant_id=saved.tenant_id,
                    name=saved.name,
                    email=saved.email,
                )
            )

        return self._to_dto(saved)

    def update_contact(
        self, command: UpdateContactCommand, tenant_id: UUID
    ) -> ContactDTO:
        """Update a contact."""
        contact = self.contact_repo.get_by_id(command.contact_id, tenant_id)
        if not contact:
            raise ContactNotFoundError(command.contact_id)

        changes = {}
        if command.name is not None:
            contact.update_name(command.name)
            changes["name"] = command.name
        if command.email is not None:
            contact.update_email(command.email)
            changes["email"] = command.email
        if command.phone is not None:
            contact.update_phone(command.phone)
            changes["phone"] = command.phone
        if command.notes is not None:
            contact.notes = command.notes
            changes["notes"] = command.notes

        saved = self.contact_repo.save(contact)

        if self.event_bus and changes:
            self.event_bus.publish(
                ContactUpdated(
                    contact_id=saved.id,
                    tenant_id=saved.tenant_id,
                    changes=changes,
                )
            )

        return self._to_dto(saved)

    def get_contact(self, contact_id: UUID, tenant_id: UUID) -> ContactDTO | None:
        """Get a contact by ID."""
        contact = self.contact_repo.get_by_id(contact_id, tenant_id)
        return self._to_dto(contact) if contact else None

    def list_contacts(self, tenant_id: UUID) -> list[ContactDTO]:
        """List all contacts for a tenant."""
        contacts = self.contact_repo.get_all(tenant_id)
        return [self._to_dto(c) for c in contacts]

    def archive_contact(self, contact_id: UUID, tenant_id: UUID) -> ContactDTO:
        """Archive a contact."""
        contact = self.contact_repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise ContactNotFoundError(contact_id)

        contact.archive()
        saved = self.contact_repo.save(contact)

        if self.event_bus:
            self.event_bus.publish(
                ContactArchived(
                    contact_id=saved.id,
                    tenant_id=saved.tenant_id,
                )
            )

        return self._to_dto(saved)

    def delete_contact(self, contact_id: UUID, tenant_id: UUID) -> bool:
        """Delete a contact."""
        return self.contact_repo.delete(contact_id, tenant_id)

    def _to_dto(self, contact: Contact) -> ContactDTO:
        """Convert entity to DTO."""
        return ContactDTO(
            id=contact.id,
            tenant_id=contact.tenant_id,
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            avatar_url=contact.avatar_url,
            notes=contact.notes,
            status=contact.status.value,
            linked_user_id=contact.linked_user_id,
            share_status=contact.share_status.value,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )


# =============================================================================
# Contact Group Use Cases
# =============================================================================


@dataclass
class ContactGroupUseCases:
    """Use cases for contact group management."""

    group_repo: ContactGroupRepository
    contact_repo: ContactRepository

    def create_group(self, command: CreateContactGroupCommand) -> ContactGroupDTO:
        """Create a new contact group."""
        group = ContactGroup.create(
            tenant_id=command.tenant_id,
            name=command.name,
            description=command.description,
        )

        # Add members
        for member_id in command.member_ids:
            contact = self.contact_repo.get_by_id(member_id, command.tenant_id)
            if contact:
                group.add_member(contact)

        saved = self.group_repo.save(group)
        return self._to_dto(saved)

    def get_group(self, group_id: UUID, tenant_id: UUID) -> ContactGroupDTO | None:
        """Get a group by ID."""
        group = self.group_repo.get_by_id(group_id, tenant_id)
        return self._to_dto(group) if group else None

    def list_groups(self, tenant_id: UUID) -> list[ContactGroupDTO]:
        """List all groups for a tenant."""
        groups = self.group_repo.get_all(tenant_id)
        return [self._to_dto(g) for g in groups]

    def add_member(
        self, group_id: UUID, contact_id: UUID, tenant_id: UUID
    ) -> ContactGroupDTO:
        """Add a member to a group."""
        group = self.group_repo.get_by_id(group_id, tenant_id)
        if not group:
            raise ContactNotFoundError(group_id)

        contact = self.contact_repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise ContactNotFoundError(contact_id)

        group.add_member(contact)
        saved = self.group_repo.save(group)
        return self._to_dto(saved)

    def remove_member(
        self, group_id: UUID, contact_id: UUID, tenant_id: UUID
    ) -> ContactGroupDTO:
        """Remove a member from a group."""
        group = self.group_repo.get_by_id(group_id, tenant_id)
        if not group:
            raise ContactNotFoundError(group_id)

        group.remove_member(contact_id)
        saved = self.group_repo.save(group)
        return self._to_dto(saved)

    def _to_dto(self, group: ContactGroup) -> ContactGroupDTO:
        """Convert entity to DTO."""
        return ContactGroupDTO(
            id=group.id,
            tenant_id=group.tenant_id,
            name=group.name,
            description=group.description,
            member_ids=list(group.member_ids),
            member_count=group.member_count,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )


# =============================================================================
# Peer Debt Use Cases
# =============================================================================


@dataclass
class PeerDebtUseCases:
    """Use cases for peer debt management."""

    debt_repo: PeerDebtRepository
    contact_repo: ContactRepository
    settlement_repo: SettlementRepository
    event_bus: "EventBus | None" = None

    def create_debt(self, command: CreatePeerDebtCommand) -> PeerDebtDTO:
        """Create a new peer debt."""
        # Verify contact exists
        contact = self.contact_repo.get_by_id(command.contact_id, command.tenant_id)
        if not contact:
            raise ContactNotFoundError(command.contact_id)

        direction = DebtDirection(command.direction)
        debt = PeerDebt.create(
            tenant_id=command.tenant_id,
            contact_id=command.contact_id,
            direction=direction,
            amount=command.amount,
            currency_code=command.currency_code,
            description=command.description,
            debt_date=command.debt_date,
            due_date=command.due_date,
            notes=command.notes,
            linked_transaction_id=command.linked_transaction_id,
        )

        saved = self.debt_repo.save(debt)

        if self.event_bus:
            self.event_bus.publish(
                PeerDebtCreated(
                    debt_id=saved.id,
                    tenant_id=saved.tenant_id,
                    contact_id=saved.contact_id,
                    direction=saved.direction.value,
                    amount=saved.amount,
                    currency_code=saved.currency_code,
                )
            )

        return self._to_dto(saved, contact.name)

    def get_debt(self, debt_id: UUID, tenant_id: UUID) -> PeerDebtDTO | None:
        """Get a debt by ID."""
        debt = self.debt_repo.get_by_id(debt_id, tenant_id)
        if not debt:
            return None

        contact = self.contact_repo.get_by_id(debt.contact_id, tenant_id)
        contact_name = contact.name if contact else None
        return self._to_dto(debt, contact_name)

    def list_debts(self, tenant_id: UUID) -> list[PeerDebtDTO]:
        """List all debts for a tenant."""
        debts = self.debt_repo.get_all(tenant_id)
        result = []
        for debt in debts:
            contact = self.contact_repo.get_by_id(debt.contact_id, tenant_id)
            contact_name = contact.name if contact else None
            result.append(self._to_dto(debt, contact_name))
        return result

    def list_active_debts(self, tenant_id: UUID) -> list[PeerDebtDTO]:
        """List all active (unsettled) debts."""
        debts = self.debt_repo.get_active(tenant_id)
        result = []
        for debt in debts:
            contact = self.contact_repo.get_by_id(debt.contact_id, tenant_id)
            contact_name = contact.name if contact else None
            result.append(self._to_dto(debt, contact_name))
        return result

    def list_debts_by_contact(
        self, contact_id: UUID, tenant_id: UUID
    ) -> list[PeerDebtDTO]:
        """List all debts with a specific contact."""
        contact = self.contact_repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise ContactNotFoundError(contact_id)

        debts = self.debt_repo.get_by_contact(contact_id, tenant_id)
        return [self._to_dto(d, contact.name) for d in debts]

    def settle_debt(
        self, command: SettleDebtCommand, tenant_id: UUID
    ) -> PeerDebtDTO:
        """Partially or fully settle a debt."""
        debt = self.debt_repo.get_by_id(command.debt_id, tenant_id)
        if not debt:
            raise DebtNotFoundError(command.debt_id)

        if debt.status == DebtStatus.SETTLED:
            raise DebtAlreadySettledError(command.debt_id)

        debt.settle(command.amount)
        saved = self.debt_repo.save(debt)

        if self.event_bus:
            self.event_bus.publish(
                PeerDebtSettled(
                    debt_id=saved.id,
                    tenant_id=saved.tenant_id,
                    settlement_amount=command.amount,
                    remaining_amount=saved.remaining_amount,
                    is_fully_settled=saved.status == DebtStatus.SETTLED,
                )
            )

        contact = self.contact_repo.get_by_id(debt.contact_id, tenant_id)
        contact_name = contact.name if contact else None
        return self._to_dto(saved, contact_name)

    def cancel_debt(self, debt_id: UUID, tenant_id: UUID) -> PeerDebtDTO:
        """Cancel a debt."""
        debt = self.debt_repo.get_by_id(debt_id, tenant_id)
        if not debt:
            raise DebtNotFoundError(debt_id)

        debt.cancel()
        saved = self.debt_repo.save(debt)

        contact = self.contact_repo.get_by_id(debt.contact_id, tenant_id)
        contact_name = contact.name if contact else None
        return self._to_dto(saved, contact_name)

    def _to_dto(self, debt: PeerDebt, contact_name: str | None) -> PeerDebtDTO:
        """Convert entity to DTO."""
        return PeerDebtDTO(
            id=debt.id,
            tenant_id=debt.tenant_id,
            contact_id=debt.contact_id,
            contact_name=contact_name,
            direction=debt.direction.value,
            amount=debt.amount,
            currency_code=debt.currency_code,
            settled_amount=debt.settled_amount,
            remaining_amount=debt.remaining_amount,
            description=debt.description,
            debt_date=debt.debt_date,
            due_date=debt.due_date,
            status=debt.status.value,
            linked_transaction_id=debt.linked_transaction_id,
            notes=debt.notes,
            created_at=debt.created_at,
            updated_at=debt.updated_at,
        )


# =============================================================================
# Expense Group Use Cases
# =============================================================================


@dataclass
class ExpenseGroupUseCases:
    """Use cases for expense group management."""

    group_repo: ExpenseGroupRepository
    contact_repo: ContactRepository
    expense_repo: GroupExpenseRepository
    event_bus: "EventBus | None" = None

    def create_group(self, command: CreateExpenseGroupCommand) -> ExpenseGroupDTO:
        """Create a new expense group."""
        group = ExpenseGroup.create(
            tenant_id=command.tenant_id,
            name=command.name,
            default_currency=command.default_currency,
            description=command.description,
            include_self=command.include_self,
        )

        # Add members
        for contact_id in command.member_contact_ids:
            contact = self.contact_repo.get_by_id(contact_id, command.tenant_id)
            if contact:
                group.add_member(contact)

        saved = self.group_repo.save(group)

        if self.event_bus:
            self.event_bus.publish(
                ExpenseGroupCreated(
                    group_id=saved.id,
                    tenant_id=saved.tenant_id,
                    name=saved.name,
                    member_count=saved.total_members,
                )
            )

        return self._to_dto(saved)

    def get_group(self, group_id: UUID, tenant_id: UUID) -> ExpenseGroupDTO | None:
        """Get an expense group by ID."""
        group = self.group_repo.get_by_id(group_id, tenant_id)
        return self._to_dto(group) if group else None

    def list_groups(self, tenant_id: UUID) -> list[ExpenseGroupDTO]:
        """List all expense groups for a tenant."""
        groups = self.group_repo.get_all(tenant_id)
        return [self._to_dto(g) for g in groups]

    def add_member(
        self, group_id: UUID, contact_id: UUID, tenant_id: UUID
    ) -> ExpenseGroupDTO:
        """Add a member to an expense group."""
        group = self.group_repo.get_by_id(group_id, tenant_id)
        if not group:
            raise ExpenseGroupNotFoundError(group_id)

        contact = self.contact_repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise ContactNotFoundError(contact_id)

        group.add_member(contact)
        saved = self.group_repo.save(group)

        if self.event_bus:
            self.event_bus.publish(
                ExpenseGroupMemberAdded(
                    group_id=saved.id,
                    tenant_id=saved.tenant_id,
                    contact_id=contact_id,
                )
            )

        return self._to_dto(saved)

    def remove_member(
        self, group_id: UUID, contact_id: UUID, tenant_id: UUID
    ) -> ExpenseGroupDTO:
        """Remove a member from an expense group."""
        group = self.group_repo.get_by_id(group_id, tenant_id)
        if not group:
            raise ExpenseGroupNotFoundError(group_id)

        group.remove_member(contact_id)
        saved = self.group_repo.save(group)
        return self._to_dto(saved)

    def _to_dto(self, group: ExpenseGroup) -> ExpenseGroupDTO:
        """Convert entity to DTO."""
        return ExpenseGroupDTO(
            id=group.id,
            tenant_id=group.tenant_id,
            name=group.name,
            description=group.description,
            default_currency=group.default_currency,
            member_contact_ids=list(group.member_contact_ids),
            include_self=group.include_self,
            total_members=group.total_members,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )


# =============================================================================
# Group Expense Use Cases
# =============================================================================


@dataclass
class GroupExpenseUseCases:
    """Use cases for group expense management."""

    expense_repo: GroupExpenseRepository
    group_repo: ExpenseGroupRepository
    contact_repo: ContactRepository
    event_bus: "EventBus | None" = None

    def create_expense(self, command: CreateGroupExpenseCommand) -> GroupExpenseDTO:
        """Create a new group expense."""
        # Verify group exists
        group = self.group_repo.get_by_id(command.group_id, command.tenant_id)
        if not group:
            raise ExpenseGroupNotFoundError(command.group_id)

        # Determine split method
        split_method = SplitMethod(command.split_method)

        # Create base expense
        expense = GroupExpense.create(
            tenant_id=command.tenant_id,
            group_id=command.group_id,
            description=command.description,
            total_amount=command.total_amount,
            currency_code=command.currency_code,
            paid_by_owner=command.paid_by_owner,
            paid_by_contact_id=command.paid_by_contact_id,
            split_method=split_method,
            expense_date=command.expense_date,
            notes=command.notes,
        )

        # Calculate splits
        if split_method == SplitMethod.EQUAL:
            expense.calculate_equal_splits(
                member_contact_ids=list(group.member_contact_ids),
                include_owner=group.include_self,
            )
        elif split_method == SplitMethod.EXACT:
            if not command.exact_splits:
                raise InvalidSplitTotalError(
                    expected=command.total_amount,
                    actual=Decimal("0"),
                )
            expense.set_exact_splits(command.exact_splits)

        saved = self.expense_repo.save(expense)

        if self.event_bus:
            self.event_bus.publish(
                GroupExpenseCreated(
                    expense_id=saved.id,
                    tenant_id=saved.tenant_id,
                    group_id=saved.group_id,
                    description=saved.description,
                    total_amount=saved.total_amount,
                    currency_code=saved.currency_code,
                    split_count=len(saved.splits),
                )
            )

        return self._to_dto(saved)

    def get_expense(self, expense_id: UUID, tenant_id: UUID) -> GroupExpenseDTO | None:
        """Get an expense by ID."""
        expense = self.expense_repo.get_by_id(expense_id, tenant_id)
        return self._to_dto(expense) if expense else None

    def list_expenses_by_group(
        self, group_id: UUID, tenant_id: UUID
    ) -> list[GroupExpenseDTO]:
        """List all expenses in a group."""
        expenses = self.expense_repo.get_by_group(group_id, tenant_id)
        return [self._to_dto(e) for e in expenses]

    def cancel_expense(self, expense_id: UUID, tenant_id: UUID) -> GroupExpenseDTO:
        """Cancel an expense."""
        expense = self.expense_repo.get_by_id(expense_id, tenant_id)
        if not expense:
            raise GroupExpenseNotFoundError(expense_id)

        expense.cancel()
        saved = self.expense_repo.save(expense)
        return self._to_dto(saved)

    def _to_dto(self, expense: GroupExpense) -> GroupExpenseDTO:
        """Convert entity to DTO."""
        splits = [
            ExpenseSplitDTO(
                id=s.id,
                expense_id=s.expense_id,
                contact_id=s.contact_id,
                is_owner=s.is_owner,
                share_amount=s.share_amount,
                settled_amount=s.settled_amount,
                remaining_amount=s.remaining_amount,
                status=s.status.value,
            )
            for s in expense.splits
        ]

        return GroupExpenseDTO(
            id=expense.id,
            tenant_id=expense.tenant_id,
            group_id=expense.group_id,
            description=expense.description,
            total_amount=expense.total_amount,
            currency_code=expense.currency_code,
            paid_by_contact_id=expense.paid_by_contact_id,
            paid_by_owner=expense.paid_by_owner,
            split_method=expense.split_method.value,
            expense_date=expense.expense_date,
            splits=splits,
            status=expense.status.value,
            notes=expense.notes,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )


# =============================================================================
# Settlement Use Cases
# =============================================================================


@dataclass
class SettlementUseCases:
    """Use cases for settlement management."""

    settlement_repo: SettlementRepository
    debt_repo: PeerDebtRepository
    expense_repo: GroupExpenseRepository
    contact_repo: ContactRepository
    event_bus: "EventBus | None" = None

    def create_settlement(self, command: CreateSettlementCommand) -> SettlementDTO:
        """Create a settlement."""
        # Determine direction
        if command.owner_pays and command.owner_receives:
            raise ValueError("Cannot both pay and receive")
        if not command.owner_pays and not command.owner_receives:
            raise ValueError("Must specify owner_pays or owner_receives")

        from_is_owner = command.owner_pays
        to_is_owner = command.owner_receives

        settlement = Settlement.create(
            tenant_id=command.tenant_id,
            from_is_owner=from_is_owner,
            to_is_owner=to_is_owner,
            from_contact_id=command.contact_id if not from_is_owner else None,
            to_contact_id=command.contact_id if not to_is_owner else None,
            amount=command.amount,
            currency_code=command.currency_code,
            method=command.method,
            settlement_date=command.settlement_date,
            notes=command.notes,
        )

        # Link to debts
        for debt_id in command.linked_debt_ids:
            debt = self.debt_repo.get_by_id(debt_id, command.tenant_id)
            if debt:
                settlement.link_to_debt(debt)

        # Link to splits
        for split_id in command.linked_split_ids:
            # Find the split in expenses
            for expense in self.expense_repo.get_all(command.tenant_id):
                for split in expense.splits:
                    if split.id == split_id:
                        settlement.link_to_split(split)
                        break

        saved = self.settlement_repo.save(settlement)

        if self.event_bus:
            self.event_bus.publish(
                SettlementCreated(
                    settlement_id=saved.id,
                    tenant_id=saved.tenant_id,
                    from_is_owner=saved.from_is_owner,
                    to_is_owner=saved.to_is_owner,
                    from_contact_id=saved.from_contact_id,
                    to_contact_id=saved.to_contact_id,
                    amount=saved.amount,
                    currency_code=saved.currency_code,
                    linked_debt_count=len(saved.linked_debt_ids),
                    linked_split_count=len(saved.linked_split_ids),
                )
            )

        return self._to_dto(saved)

    def get_settlement(
        self, settlement_id: UUID, tenant_id: UUID
    ) -> SettlementDTO | None:
        """Get a settlement by ID."""
        settlement = self.settlement_repo.get_by_id(settlement_id, tenant_id)
        return self._to_dto(settlement) if settlement else None

    def list_settlements(self, tenant_id: UUID) -> list[SettlementDTO]:
        """List all settlements for a tenant."""
        settlements = self.settlement_repo.get_all(tenant_id)
        return [self._to_dto(s) for s in settlements]

    def list_settlements_by_contact(
        self, contact_id: UUID, tenant_id: UUID
    ) -> list[SettlementDTO]:
        """List all settlements with a specific contact."""
        settlements = self.settlement_repo.get_by_contact(contact_id, tenant_id)
        return [self._to_dto(s) for s in settlements]

    def _to_dto(self, settlement: Settlement) -> SettlementDTO:
        """Convert entity to DTO."""
        return SettlementDTO(
            id=settlement.id,
            tenant_id=settlement.tenant_id,
            from_contact_id=settlement.from_contact_id,
            to_contact_id=settlement.to_contact_id,
            from_is_owner=settlement.from_is_owner,
            to_is_owner=settlement.to_is_owner,
            amount=settlement.amount,
            currency_code=settlement.currency_code,
            method=settlement.method,
            settlement_date=settlement.settlement_date,
            linked_debt_ids=list(settlement.linked_debt_ids),
            linked_split_ids=list(settlement.linked_split_ids),
            notes=settlement.notes,
            created_at=settlement.created_at,
        )


# =============================================================================
# Balance Calculation Use Cases
# =============================================================================


@dataclass
class BalanceUseCases:
    """Use cases for balance calculations."""

    debt_repo: PeerDebtRepository
    settlement_repo: SettlementRepository
    expense_repo: GroupExpenseRepository
    group_repo: ExpenseGroupRepository
    contact_repo: ContactRepository

    def get_contact_balance(
        self, contact_id: UUID, tenant_id: UUID, currency_code: str
    ) -> ContactBalanceDTO:
        """Get balance with a specific contact."""
        contact = self.contact_repo.get_by_id(contact_id, tenant_id)
        if not contact:
            raise ContactNotFoundError(contact_id)

        debts = self.debt_repo.get_by_contact(contact_id, tenant_id)
        settlements = self.settlement_repo.get_by_contact(contact_id, tenant_id)

        balance = DebtCalculator.calculate_contact_balance(
            debts=debts,
            settlements=settlements,
            contact_id=contact_id,
            currency_code=currency_code,
        )

        return ContactBalanceDTO(
            contact_id=balance.contact_id,
            contact_name=contact.name,
            currency_code=balance.currency_code,
            total_lent=balance.total_lent,
            total_borrowed=balance.total_borrowed,
            total_settled_to_them=balance.total_settled_to_them,
            total_settled_from_them=balance.total_settled_from_them,
            net_balance=balance.net_balance,
            they_owe_you=balance.they_owe_you,
            you_owe_them=balance.you_owe_them,
        )

    def get_all_contact_balances(
        self, tenant_id: UUID, currency_code: str
    ) -> list[ContactBalanceDTO]:
        """Get balances with all contacts."""
        debts = self.debt_repo.get_all(tenant_id)
        settlements = self.settlement_repo.get_all(tenant_id)

        balances = DebtCalculator.calculate_all_balances(
            debts=debts,
            settlements=settlements,
            currency_code=currency_code,
        )

        result = []
        for contact_id, balance in balances.items():
            contact = self.contact_repo.get_by_id(contact_id, tenant_id)
            contact_name = contact.name if contact else None

            result.append(
                ContactBalanceDTO(
                    contact_id=balance.contact_id,
                    contact_name=contact_name,
                    currency_code=balance.currency_code,
                    total_lent=balance.total_lent,
                    total_borrowed=balance.total_borrowed,
                    total_settled_to_them=balance.total_settled_to_them,
                    total_settled_from_them=balance.total_settled_from_them,
                    net_balance=balance.net_balance,
                    they_owe_you=balance.they_owe_you,
                    you_owe_them=balance.you_owe_them,
                )
            )

        return result

    def get_group_balance(
        self, group_id: UUID, tenant_id: UUID
    ) -> GroupBalanceDTO:
        """Get balance for an expense group."""
        group = self.group_repo.get_by_id(group_id, tenant_id)
        if not group:
            raise ExpenseGroupNotFoundError(group_id)

        expenses = self.expense_repo.get_by_group(group_id, tenant_id)
        balance = GroupBalanceCalculator.calculate(expenses, group.default_currency)

        # Convert to DTOs with names
        entries = []
        for entry in balance.entries:
            from_name = "You" if entry.from_contact_id is None else None
            to_name = "You" if entry.to_contact_id is None else None

            if entry.from_contact_id:
                contact = self.contact_repo.get_by_id(entry.from_contact_id, tenant_id)
                from_name = contact.name if contact else None
            if entry.to_contact_id:
                contact = self.contact_repo.get_by_id(entry.to_contact_id, tenant_id)
                to_name = contact.name if contact else None

            entries.append(
                GroupBalanceEntryDTO(
                    from_contact_id=entry.from_contact_id,
                    from_name=from_name,
                    to_contact_id=entry.to_contact_id,
                    to_name=to_name,
                    amount=entry.amount,
                )
            )

        return GroupBalanceDTO(
            group_id=balance.group_id,
            group_name=group.name,
            currency_code=balance.currency_code,
            entries=entries,
            total_expenses=balance.total_expenses,
        )

    def get_settlement_suggestions(
        self, tenant_id: UUID, currency_code: str
    ) -> list[SettlementSuggestionDTO]:
        """Get suggestions for settling all balances."""
        debts = self.debt_repo.get_all(tenant_id)
        settlements = self.settlement_repo.get_all(tenant_id)

        balances = DebtCalculator.calculate_all_balances(
            debts=debts,
            settlements=settlements,
            currency_code=currency_code,
        )

        suggestions = SettlementSuggestionService.suggest_all(balances)

        result = []
        for suggestion in suggestions:
            from_name = "You" if suggestion.from_contact_id is None else None
            to_name = "You" if suggestion.to_contact_id is None else None

            if suggestion.from_contact_id:
                contact = self.contact_repo.get_by_id(suggestion.from_contact_id, tenant_id)
                from_name = contact.name if contact else None
            if suggestion.to_contact_id:
                contact = self.contact_repo.get_by_id(suggestion.to_contact_id, tenant_id)
                to_name = contact.name if contact else None

            result.append(
                SettlementSuggestionDTO(
                    from_contact_id=suggestion.from_contact_id,
                    from_name=from_name,
                    to_contact_id=suggestion.to_contact_id,
                    to_name=to_name,
                    amount=suggestion.amount,
                    currency_code=currency_code,
                )
            )

        return result
