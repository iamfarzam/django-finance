"""Repository interfaces for the finance module.

These interfaces define the contract between the application layer
and the infrastructure layer. They enable dependency inversion and
make the domain logic testable without a database.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from modules.finance.domain.entities import (
        Account,
        Asset,
        Category,
        Liability,
        Loan,
        Transaction,
        Transfer,
    )
    from modules.finance.domain.events import BaseEvent


class AccountRepository(ABC):
    """Repository interface for Account persistence."""

    @abstractmethod
    async def get_by_id(self, account_id: UUID, tenant_id: UUID) -> Account | None:
        """Get an account by ID.

        Args:
            account_id: The account ID.
            tenant_id: The tenant ID for isolation.

        Returns:
            Account if found, None otherwise.
        """
        ...

    @abstractmethod
    async def get_all(self, tenant_id: UUID) -> list[Account]:
        """Get all accounts for a tenant.

        Args:
            tenant_id: The tenant ID.

        Returns:
            List of accounts.
        """
        ...

    @abstractmethod
    async def get_active(self, tenant_id: UUID) -> list[Account]:
        """Get all active accounts for a tenant.

        Args:
            tenant_id: The tenant ID.

        Returns:
            List of active accounts.
        """
        ...

    @abstractmethod
    async def count(self, tenant_id: UUID) -> int:
        """Count accounts for a tenant.

        Args:
            tenant_id: The tenant ID.

        Returns:
            Number of accounts.
        """
        ...

    @abstractmethod
    async def save(self, account: Account) -> Account:
        """Save an account (create or update).

        Args:
            account: The account to save.

        Returns:
            Saved account.
        """
        ...

    @abstractmethod
    async def delete(self, account_id: UUID, tenant_id: UUID) -> bool:
        """Delete an account.

        Args:
            account_id: The account ID.
            tenant_id: The tenant ID.

        Returns:
            True if deleted, False if not found.
        """
        ...


class TransactionRepository(ABC):
    """Repository interface for Transaction persistence."""

    @abstractmethod
    async def get_by_id(
        self, transaction_id: UUID, tenant_id: UUID
    ) -> Transaction | None:
        """Get a transaction by ID.

        Args:
            transaction_id: The transaction ID.
            tenant_id: The tenant ID.

        Returns:
            Transaction if found, None otherwise.
        """
        ...

    @abstractmethod
    async def get_by_account(
        self,
        account_id: UUID,
        tenant_id: UUID,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get transactions for an account.

        Args:
            account_id: The account ID.
            tenant_id: The tenant ID.
            start_date: Optional start date filter.
            end_date: Optional end date filter.
            limit: Maximum number of transactions.
            offset: Number of transactions to skip.

        Returns:
            List of transactions.
        """
        ...

    @abstractmethod
    async def get_by_idempotency_key(
        self, key: str, tenant_id: UUID
    ) -> Transaction | None:
        """Get a transaction by idempotency key.

        Args:
            key: The idempotency key.
            tenant_id: The tenant ID.

        Returns:
            Transaction if found, None otherwise.
        """
        ...

    @abstractmethod
    async def save(self, transaction: Transaction) -> Transaction:
        """Save a transaction (create or update).

        Args:
            transaction: The transaction to save.

        Returns:
            Saved transaction.
        """
        ...

    @abstractmethod
    async def save_batch(self, transactions: list[Transaction]) -> list[Transaction]:
        """Save multiple transactions atomically.

        Args:
            transactions: The transactions to save.

        Returns:
            Saved transactions.
        """
        ...


class TransferRepository(ABC):
    """Repository interface for Transfer persistence."""

    @abstractmethod
    async def get_by_id(self, transfer_id: UUID, tenant_id: UUID) -> Transfer | None:
        """Get a transfer by ID."""
        ...

    @abstractmethod
    async def save(self, transfer: Transfer) -> Transfer:
        """Save a transfer."""
        ...


class AssetRepository(ABC):
    """Repository interface for Asset persistence."""

    @abstractmethod
    async def get_by_id(self, asset_id: UUID, tenant_id: UUID) -> Asset | None:
        """Get an asset by ID."""
        ...

    @abstractmethod
    async def get_all(self, tenant_id: UUID) -> list[Asset]:
        """Get all assets for a tenant."""
        ...

    @abstractmethod
    async def save(self, asset: Asset) -> Asset:
        """Save an asset."""
        ...

    @abstractmethod
    async def delete(self, asset_id: UUID, tenant_id: UUID) -> bool:
        """Delete an asset."""
        ...


class LiabilityRepository(ABC):
    """Repository interface for Liability persistence."""

    @abstractmethod
    async def get_by_id(
        self, liability_id: UUID, tenant_id: UUID
    ) -> Liability | None:
        """Get a liability by ID."""
        ...

    @abstractmethod
    async def get_all(self, tenant_id: UUID) -> list[Liability]:
        """Get all liabilities for a tenant."""
        ...

    @abstractmethod
    async def save(self, liability: Liability) -> Liability:
        """Save a liability."""
        ...

    @abstractmethod
    async def delete(self, liability_id: UUID, tenant_id: UUID) -> bool:
        """Delete a liability."""
        ...


class LoanRepository(ABC):
    """Repository interface for Loan persistence."""

    @abstractmethod
    async def get_by_id(self, loan_id: UUID, tenant_id: UUID) -> Loan | None:
        """Get a loan by ID."""
        ...

    @abstractmethod
    async def get_all(self, tenant_id: UUID) -> list[Loan]:
        """Get all loans for a tenant."""
        ...

    @abstractmethod
    async def get_active(self, tenant_id: UUID) -> list[Loan]:
        """Get all active loans for a tenant."""
        ...

    @abstractmethod
    async def save(self, loan: Loan) -> Loan:
        """Save a loan."""
        ...

    @abstractmethod
    async def delete(self, loan_id: UUID, tenant_id: UUID) -> bool:
        """Delete a loan."""
        ...


class CategoryRepository(ABC):
    """Repository interface for Category persistence."""

    @abstractmethod
    async def get_by_id(self, category_id: UUID, tenant_id: UUID) -> Category | None:
        """Get a category by ID."""
        ...

    @abstractmethod
    async def get_all(self, tenant_id: UUID) -> list[Category]:
        """Get all categories for a tenant (including system categories)."""
        ...

    @abstractmethod
    async def get_by_name(self, name: str, tenant_id: UUID) -> Category | None:
        """Get a category by name."""
        ...

    @abstractmethod
    async def save(self, category: Category) -> Category:
        """Save a category."""
        ...

    @abstractmethod
    async def delete(self, category_id: UUID, tenant_id: UUID) -> bool:
        """Delete a category."""
        ...


class IdempotencyRepository(ABC):
    """Repository interface for idempotency key tracking."""

    @abstractmethod
    async def exists(self, key: str, tenant_id: UUID) -> bool:
        """Check if an idempotency key exists.

        Args:
            key: The idempotency key.
            tenant_id: The tenant ID.

        Returns:
            True if key exists, False otherwise.
        """
        ...

    @abstractmethod
    async def save(
        self,
        key: str,
        tenant_id: UUID,
        resource_id: UUID,
        resource_type: str,
    ) -> None:
        """Save an idempotency key.

        Args:
            key: The idempotency key.
            tenant_id: The tenant ID.
            resource_id: The ID of the created resource.
            resource_type: The type of resource (e.g., "transaction").
        """
        ...

    @abstractmethod
    async def get_resource_id(self, key: str, tenant_id: UUID) -> UUID | None:
        """Get the resource ID for an idempotency key.

        Args:
            key: The idempotency key.
            tenant_id: The tenant ID.

        Returns:
            Resource ID if found, None otherwise.
        """
        ...


class BalanceCache(ABC):
    """Interface for caching account balances."""

    @abstractmethod
    async def get(self, account_id: UUID) -> Decimal | None:
        """Get cached balance for an account.

        Args:
            account_id: The account ID.

        Returns:
            Cached balance or None if not cached.
        """
        ...

    @abstractmethod
    async def set(self, account_id: UUID, balance: Decimal) -> None:
        """Cache balance for an account.

        Args:
            account_id: The account ID.
            balance: The balance to cache.
        """
        ...

    @abstractmethod
    async def invalidate(self, account_id: UUID) -> None:
        """Invalidate cached balance for an account.

        Args:
            account_id: The account ID.
        """
        ...


class EventPublisher(ABC):
    """Interface for publishing domain events."""

    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """Publish an event.

        Args:
            event: The event to publish.
        """
        ...

    @abstractmethod
    async def publish_batch(self, events: list[BaseEvent]) -> None:
        """Publish multiple events.

        Args:
            events: The events to publish.
        """
        ...
