"""Base models for Django Finance.

This module provides abstract base models that implement common patterns
used across the application, including UUID primary keys, timestamps,
tenant isolation, and soft delete support.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, TypeVar

from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models.manager import Manager

T = TypeVar("T", bound="BaseModel")


class BaseQuerySet(models.QuerySet[T]):
    """Base QuerySet with common utility methods."""

    def active(self) -> "BaseQuerySet[T]":
        """Filter to active (non-deleted) records if model supports soft delete."""
        if hasattr(self.model, "is_deleted"):
            return self.filter(is_deleted=False)
        return self


class TenantQuerySet(BaseQuerySet[T]):
    """QuerySet with tenant scoping support.

    Automatically filters queries by tenant_id when a tenant context is set.
    """

    _tenant_id: uuid.UUID | None = None

    def for_tenant(self, tenant_id: uuid.UUID) -> "TenantQuerySet[T]":
        """Filter queryset to a specific tenant.

        Args:
            tenant_id: The tenant UUID to filter by.

        Returns:
            Filtered queryset for the specified tenant.
        """
        return self.filter(tenant_id=tenant_id)


class BaseManager(models.Manager[T]):
    """Base manager using BaseQuerySet."""

    def get_queryset(self) -> BaseQuerySet[T]:
        """Return the custom queryset."""
        return BaseQuerySet(self.model, using=self._db)

    def active(self) -> BaseQuerySet[T]:
        """Return only active records."""
        return self.get_queryset().active()


class TenantManager(models.Manager[T]):
    """Manager with tenant scoping support.

    This manager provides methods to scope queries to a specific tenant.
    Use this manager for all tenant-scoped models.
    """

    def get_queryset(self) -> TenantQuerySet[T]:
        """Return the custom queryset."""
        return TenantQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant_id: uuid.UUID) -> TenantQuerySet[T]:
        """Get queryset filtered to a specific tenant.

        Args:
            tenant_id: The tenant UUID to filter by.

        Returns:
            Filtered queryset for the specified tenant.
        """
        return self.get_queryset().for_tenant(tenant_id)


class BaseModel(models.Model):
    """Abstract base model with UUID primary key and timestamps.

    All models in the application should inherit from this base model
    to ensure consistent ID generation and timestamp tracking.

    Attributes:
        id: UUID primary key, auto-generated.
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp when this record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated.",
    )

    objects: Manager[Any] = BaseManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class TenantModel(BaseModel):
    """Abstract model with tenant isolation.

    All tenant-scoped data must inherit from this model to ensure
    proper data isolation between tenants.

    Attributes:
        tenant_id: Foreign key to the tenant this record belongs to.
    """

    tenant_id = models.UUIDField(
        db_index=True,
        help_text="The tenant this record belongs to.",
    )

    objects: Manager[Any] = TenantManager()

    class Meta:
        abstract = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, tenant_id={self.tenant_id})>"


class SoftDeleteQuerySet(TenantQuerySet[T]):
    """QuerySet with soft delete support."""

    def delete(self) -> tuple[int, dict[str, int]]:
        """Soft delete records instead of hard delete.

        Returns:
            Tuple of (count, dict of deleted types).
        """
        count = self.update(is_deleted=True, deleted_at=timezone.now())
        return count, {self.model._meta.label: count}

    def hard_delete(self) -> tuple[int, dict[str, int]]:
        """Permanently delete records.

        Returns:
            Tuple of (count, dict of deleted types).
        """
        return super().delete()

    def deleted(self) -> "SoftDeleteQuerySet[T]":
        """Filter to deleted records only."""
        return self.filter(is_deleted=True)

    def with_deleted(self) -> "SoftDeleteQuerySet[T]":
        """Include deleted records in the queryset."""
        return self.all()


class SoftDeleteManager(TenantManager[T]):
    """Manager that excludes soft-deleted records by default."""

    def get_queryset(self) -> SoftDeleteQuerySet[T]:
        """Return queryset excluding deleted records."""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def deleted(self) -> SoftDeleteQuerySet[T]:
        """Return only deleted records."""
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()

    def with_deleted(self) -> SoftDeleteQuerySet[T]:
        """Return all records including deleted."""
        return SoftDeleteQuerySet(self.model, using=self._db).with_deleted()


class SoftDeleteModel(TenantModel):
    """Abstract model with soft delete support.

    Records are not physically deleted but marked as deleted.
    This allows for recovery and audit trail.

    Attributes:
        is_deleted: Whether the record has been soft deleted.
        deleted_at: Timestamp when the record was soft deleted.
    """

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this record has been soft deleted.",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when this record was soft deleted.",
    )

    objects: Manager[Any] = SoftDeleteManager()
    all_objects: Manager[Any] = TenantManager()

    class Meta:
        abstract = True

    def delete(self, using: str | None = None, keep_parents: bool = False) -> None:
        """Soft delete the record.

        Args:
            using: Database alias to use.
            keep_parents: Unused, kept for API compatibility.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using, update_fields=["is_deleted", "deleted_at", "updated_at"])

    def hard_delete(
        self, using: str | None = None, keep_parents: bool = False
    ) -> tuple[int, dict[str, int]]:
        """Permanently delete the record.

        Args:
            using: Database alias to use.
            keep_parents: Whether to keep parent records.

        Returns:
            Tuple of (count, dict of deleted types).
        """
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self, using: str | None = None) -> None:
        """Restore a soft-deleted record.

        Args:
            using: Database alias to use.
        """
        self.is_deleted = False
        self.deleted_at = None
        self.save(using=using, update_fields=["is_deleted", "deleted_at", "updated_at"])
