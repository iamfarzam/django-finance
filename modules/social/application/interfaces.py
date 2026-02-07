"""Repository interfaces for the social finance module.

These abstract interfaces define the contract for data persistence.
Implementations are provided in the infrastructure layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from modules.social.domain.entities import (
        Contact,
        ContactGroup,
        ExpenseGroup,
        ExpenseSplit,
        GroupExpense,
        PeerDebt,
        Settlement,
    )


class ContactRepository(ABC):
    """Abstract repository for Contact persistence."""

    @abstractmethod
    def get_by_id(self, contact_id: UUID, tenant_id: UUID) -> "Contact | None":
        """Get a contact by ID."""
        pass

    @abstractmethod
    def get_all(self, tenant_id: UUID) -> list["Contact"]:
        """Get all contacts for a tenant."""
        pass

    @abstractmethod
    def get_by_email(self, email: str, tenant_id: UUID) -> "Contact | None":
        """Get a contact by email."""
        pass

    @abstractmethod
    def get_by_linked_user(self, user_id: UUID) -> list["Contact"]:
        """Get all contacts linked to a user."""
        pass

    @abstractmethod
    def save(self, contact: "Contact") -> "Contact":
        """Save a contact."""
        pass

    @abstractmethod
    def delete(self, contact_id: UUID, tenant_id: UUID) -> bool:
        """Delete a contact."""
        pass


class ContactGroupRepository(ABC):
    """Abstract repository for ContactGroup persistence."""

    @abstractmethod
    def get_by_id(self, group_id: UUID, tenant_id: UUID) -> "ContactGroup | None":
        """Get a group by ID."""
        pass

    @abstractmethod
    def get_all(self, tenant_id: UUID) -> list["ContactGroup"]:
        """Get all groups for a tenant."""
        pass

    @abstractmethod
    def get_by_member(self, contact_id: UUID, tenant_id: UUID) -> list["ContactGroup"]:
        """Get all groups a contact is a member of."""
        pass

    @abstractmethod
    def save(self, group: "ContactGroup") -> "ContactGroup":
        """Save a group."""
        pass

    @abstractmethod
    def delete(self, group_id: UUID, tenant_id: UUID) -> bool:
        """Delete a group."""
        pass


class PeerDebtRepository(ABC):
    """Abstract repository for PeerDebt persistence."""

    @abstractmethod
    def get_by_id(self, debt_id: UUID, tenant_id: UUID) -> "PeerDebt | None":
        """Get a debt by ID."""
        pass

    @abstractmethod
    def get_all(self, tenant_id: UUID) -> list["PeerDebt"]:
        """Get all debts for a tenant."""
        pass

    @abstractmethod
    def get_by_contact(self, contact_id: UUID, tenant_id: UUID) -> list["PeerDebt"]:
        """Get all debts with a specific contact."""
        pass

    @abstractmethod
    def get_active(self, tenant_id: UUID) -> list["PeerDebt"]:
        """Get all active (unsettled) debts."""
        pass

    @abstractmethod
    def save(self, debt: "PeerDebt") -> "PeerDebt":
        """Save a debt."""
        pass

    @abstractmethod
    def delete(self, debt_id: UUID, tenant_id: UUID) -> bool:
        """Delete a debt."""
        pass


class ExpenseGroupRepository(ABC):
    """Abstract repository for ExpenseGroup persistence."""

    @abstractmethod
    def get_by_id(self, group_id: UUID, tenant_id: UUID) -> "ExpenseGroup | None":
        """Get an expense group by ID."""
        pass

    @abstractmethod
    def get_all(self, tenant_id: UUID) -> list["ExpenseGroup"]:
        """Get all expense groups for a tenant."""
        pass

    @abstractmethod
    def save(self, group: "ExpenseGroup") -> "ExpenseGroup":
        """Save an expense group."""
        pass

    @abstractmethod
    def delete(self, group_id: UUID, tenant_id: UUID) -> bool:
        """Delete an expense group."""
        pass


class GroupExpenseRepository(ABC):
    """Abstract repository for GroupExpense persistence."""

    @abstractmethod
    def get_by_id(self, expense_id: UUID, tenant_id: UUID) -> "GroupExpense | None":
        """Get an expense by ID."""
        pass

    @abstractmethod
    def get_by_group(self, group_id: UUID, tenant_id: UUID) -> list["GroupExpense"]:
        """Get all expenses in a group."""
        pass

    @abstractmethod
    def get_all(self, tenant_id: UUID) -> list["GroupExpense"]:
        """Get all expenses for a tenant."""
        pass

    @abstractmethod
    def save(self, expense: "GroupExpense") -> "GroupExpense":
        """Save an expense with its splits."""
        pass

    @abstractmethod
    def delete(self, expense_id: UUID, tenant_id: UUID) -> bool:
        """Delete an expense."""
        pass


class SettlementRepository(ABC):
    """Abstract repository for Settlement persistence."""

    @abstractmethod
    def get_by_id(self, settlement_id: UUID, tenant_id: UUID) -> "Settlement | None":
        """Get a settlement by ID."""
        pass

    @abstractmethod
    def get_all(self, tenant_id: UUID) -> list["Settlement"]:
        """Get all settlements for a tenant."""
        pass

    @abstractmethod
    def get_by_contact(
        self, contact_id: UUID, tenant_id: UUID
    ) -> list["Settlement"]:
        """Get all settlements with a specific contact."""
        pass

    @abstractmethod
    def get_by_debt(self, debt_id: UUID) -> list["Settlement"]:
        """Get all settlements linked to a debt."""
        pass

    @abstractmethod
    def save(self, settlement: "Settlement") -> "Settlement":
        """Save a settlement."""
        pass

    @abstractmethod
    def delete(self, settlement_id: UUID, tenant_id: UUID) -> bool:
        """Delete a settlement."""
        pass
