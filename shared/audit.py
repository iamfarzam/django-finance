"""Audit logging for the Django Finance platform.

This module provides audit logging functionality for tracking
business operations on financial data.

Audit logs are required for compliance and regulatory purposes.
Retention periods:
- Financial operations: 7 years
- Security operations: 2 years
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from django.http import HttpRequest


logger = structlog.get_logger(__name__)


class AuditAction(str, Enum):
    """Enumeration of auditable actions."""

    # Account operations
    ACCOUNT_CREATE = "account.create"
    ACCOUNT_UPDATE = "account.update"
    ACCOUNT_CLOSE = "account.close"
    ACCOUNT_REOPEN = "account.reopen"
    ACCOUNT_DELETE = "account.delete"

    # Transaction operations
    TRANSACTION_CREATE = "transaction.create"
    TRANSACTION_POST = "transaction.post"
    TRANSACTION_VOID = "transaction.void"
    TRANSACTION_ADJUST = "transaction.adjust"

    # Transfer operations
    TRANSFER_CREATE = "transfer.create"

    # Asset operations
    ASSET_CREATE = "asset.create"
    ASSET_UPDATE = "asset.update"
    ASSET_VALUE_UPDATE = "asset.value_update"
    ASSET_DELETE = "asset.delete"

    # Liability operations
    LIABILITY_CREATE = "liability.create"
    LIABILITY_UPDATE = "liability.update"
    LIABILITY_PAYMENT = "liability.payment"
    LIABILITY_DELETE = "liability.delete"

    # Loan operations
    LOAN_CREATE = "loan.create"
    LOAN_UPDATE = "loan.update"
    LOAN_PAYMENT = "loan.payment"
    LOAN_PAYOFF = "loan.payoff"
    LOAN_DELETE = "loan.delete"

    # Report operations
    REPORT_NET_WORTH = "report.net_worth"
    REPORT_CASH_FLOW = "report.cash_flow"

    # User operations (security)
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    USER_PASSWORD_CHANGE = "user.password_change"
    USER_PASSWORD_RESET = "user.password_reset"
    USER_EMAIL_VERIFY = "user.email_verify"

    # Admin operations
    ADMIN_DATA_EXPORT = "admin.data_export"
    ADMIN_DATA_DELETE = "admin.data_delete"


class AuditCategory(str, Enum):
    """Categories for audit log retention."""

    FINANCIAL = "financial"  # 7 year retention
    SECURITY = "security"  # 2 year retention
    ADMIN = "admin"  # 7 year retention


@dataclass
class AuditContext:
    """Context information for an audit event."""

    correlation_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_path: str | None = None
    request_method: str | None = None


@dataclass
class AuditEvent:
    """Represents an audit event to be logged.

    Attributes:
        id: Unique identifier for the audit event.
        timestamp: When the event occurred (UTC).
        tenant_id: Tenant the event belongs to.
        user_id: User who performed the action.
        action: The action performed.
        category: Category for retention purposes.
        resource_type: Type of resource (e.g., 'account', 'transaction').
        resource_id: ID of the affected resource.
        context: Request context information.
        details: Additional details about the event.
        changes: Before/after values for updates.
    """

    action: AuditAction
    tenant_id: uuid.UUID | str | None
    user_id: uuid.UUID | str | None
    resource_type: str
    resource_id: uuid.UUID | str | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    category: AuditCategory = AuditCategory.FINANCIAL
    context: AuditContext = field(default_factory=AuditContext)
    details: dict[str, Any] = field(default_factory=dict)
    changes: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert audit event to dictionary.

        Returns:
            Dictionary representation of the event.
        """
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action.value,
            "category": self.category.value,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "context": asdict(self.context),
            "details": self.details,
            "changes": self.changes,
        }

    def to_json(self) -> str:
        """Convert audit event to JSON string.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """Service for logging audit events.

    This class provides methods for creating and logging audit events.
    It integrates with structlog for structured logging output.
    """

    _instance: AuditLogger | None = None

    def __new__(cls) -> AuditLogger:
        """Singleton pattern for audit logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def log(self, event: AuditEvent) -> None:
        """Log an audit event.

        Args:
            event: The audit event to log.
        """
        logger.info(
            "audit_event",
            audit_id=str(event.id),
            action=event.action.value,
            category=event.category.value,
            tenant_id=str(event.tenant_id) if event.tenant_id else None,
            user_id=str(event.user_id) if event.user_id else None,
            resource_type=event.resource_type,
            resource_id=str(event.resource_id) if event.resource_id else None,
            correlation_id=event.context.correlation_id,
            details=event.details,
            changes=event.changes,
        )

    def log_action(
        self,
        action: AuditAction,
        tenant_id: uuid.UUID | str | None,
        user_id: uuid.UUID | str | None,
        resource_type: str,
        resource_id: uuid.UUID | str | None = None,
        request: HttpRequest | None = None,
        details: dict[str, Any] | None = None,
        changes: dict[str, dict[str, Any]] | None = None,
        category: AuditCategory | None = None,
    ) -> AuditEvent:
        """Log an audit action with context.

        This is a convenience method that creates and logs an audit event.

        Args:
            action: The action being performed.
            tenant_id: Tenant ID.
            user_id: User performing the action.
            resource_type: Type of resource being acted upon.
            resource_id: ID of the specific resource.
            request: HTTP request for context extraction.
            details: Additional details about the action.
            changes: Before/after values for updates.
            category: Override the default category.

        Returns:
            The created audit event.
        """
        # Determine category from action
        if category is None:
            if action.value.startswith("user."):
                category = AuditCategory.SECURITY
            elif action.value.startswith("admin."):
                category = AuditCategory.ADMIN
            else:
                category = AuditCategory.FINANCIAL

        # Extract context from request
        context = AuditContext()
        if request:
            context.correlation_id = getattr(request, "correlation_id", None)
            context.ip_address = self._get_client_ip(request)
            context.user_agent = request.headers.get("User-Agent")
            context.request_path = request.path
            context.request_method = request.method

        event = AuditEvent(
            action=action,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            category=category,
            context=context,
            details=details or {},
            changes=changes or {},
        )

        self.log(event)
        return event

    def _get_client_ip(self, request: HttpRequest) -> str | None:
        """Extract client IP from request.

        Handles X-Forwarded-For header for proxied requests.

        Args:
            request: The HTTP request.

        Returns:
            Client IP address or None.
        """
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # First IP in the chain is the original client
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def log_create(
        self,
        action: AuditAction,
        tenant_id: uuid.UUID | str | None,
        user_id: uuid.UUID | str | None,
        resource_type: str,
        resource_id: uuid.UUID | str,
        created_data: dict[str, Any],
        request: HttpRequest | None = None,
    ) -> AuditEvent:
        """Log a resource creation.

        Args:
            action: The create action.
            tenant_id: Tenant ID.
            user_id: User performing the action.
            resource_type: Type of resource created.
            resource_id: ID of the created resource.
            created_data: Data of the created resource.
            request: HTTP request for context.

        Returns:
            The created audit event.
        """
        return self.log_action(
            action=action,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            details={"created": self._sanitize_data(created_data)},
        )

    def log_update(
        self,
        action: AuditAction,
        tenant_id: uuid.UUID | str | None,
        user_id: uuid.UUID | str | None,
        resource_type: str,
        resource_id: uuid.UUID | str,
        old_data: dict[str, Any],
        new_data: dict[str, Any],
        request: HttpRequest | None = None,
    ) -> AuditEvent:
        """Log a resource update.

        Args:
            action: The update action.
            tenant_id: Tenant ID.
            user_id: User performing the action.
            resource_type: Type of resource updated.
            resource_id: ID of the updated resource.
            old_data: Data before the update.
            new_data: Data after the update.
            request: HTTP request for context.

        Returns:
            The created audit event.
        """
        # Calculate changes
        changes = {}
        sanitized_old = self._sanitize_data(old_data)
        sanitized_new = self._sanitize_data(new_data)

        for key in set(sanitized_old.keys()) | set(sanitized_new.keys()):
            old_val = sanitized_old.get(key)
            new_val = sanitized_new.get(key)
            if old_val != new_val:
                changes[key] = {"old": old_val, "new": new_val}

        return self.log_action(
            action=action,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            changes=changes,
        )

    def log_delete(
        self,
        action: AuditAction,
        tenant_id: uuid.UUID | str | None,
        user_id: uuid.UUID | str | None,
        resource_type: str,
        resource_id: uuid.UUID | str,
        deleted_data: dict[str, Any],
        request: HttpRequest | None = None,
    ) -> AuditEvent:
        """Log a resource deletion.

        Args:
            action: The delete action.
            tenant_id: Tenant ID.
            user_id: User performing the action.
            resource_type: Type of resource deleted.
            resource_id: ID of the deleted resource.
            deleted_data: Data of the deleted resource.
            request: HTTP request for context.

        Returns:
            The created audit event.
        """
        return self.log_action(
            action=action,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            details={"deleted": self._sanitize_data(deleted_data)},
        )

    def _sanitize_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize data for logging, masking sensitive fields.

        Args:
            data: Data to sanitize.

        Returns:
            Sanitized data with sensitive fields masked.
        """
        sensitive_fields = {
            "password",
            "secret",
            "token",
            "key",
            "authorization",
            "account_number",
            "ssn",
            "credit_card",
        }

        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(field in key_lower for field in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        return sanitized


# Singleton instance
audit_logger = AuditLogger()


def log_audit(
    action: AuditAction,
    tenant_id: uuid.UUID | str | None,
    user_id: uuid.UUID | str | None,
    resource_type: str,
    resource_id: uuid.UUID | str | None = None,
    request: HttpRequest | None = None,
    details: dict[str, Any] | None = None,
    changes: dict[str, dict[str, Any]] | None = None,
) -> AuditEvent:
    """Convenience function to log an audit event.

    This is a shortcut to audit_logger.log_action().

    Args:
        action: The action being performed.
        tenant_id: Tenant ID.
        user_id: User performing the action.
        resource_type: Type of resource being acted upon.
        resource_id: ID of the specific resource.
        request: HTTP request for context extraction.
        details: Additional details about the action.
        changes: Before/after values for updates.

    Returns:
        The created audit event.
    """
    return audit_logger.log_action(
        action=action,
        tenant_id=tenant_id,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        request=request,
        details=details,
        changes=changes,
    )
