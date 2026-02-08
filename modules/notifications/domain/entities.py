"""Domain entities for notifications."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from modules.notifications.domain.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)


@dataclass
class Notification:
    """A notification to be sent to a user.

    Represents a single notification that can be delivered
    through multiple channels (in-app, email, WebSocket).
    """

    # Identity
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)

    # Content
    notification_type: NotificationType = NotificationType.SYSTEM_ANNOUNCEMENT
    title: str = ""
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    action_url: str | None = None

    # Delivery
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: list[NotificationChannel] = field(default_factory=list)

    # Status tracking per channel
    status: NotificationStatus = NotificationStatus.PENDING
    email_sent: bool = False
    websocket_sent: bool = False

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    read_at: datetime | None = None
    archived_at: datetime | None = None

    @property
    def category(self) -> NotificationCategory:
        """Get the category from the notification type."""
        return self.notification_type.category

    @property
    def is_read(self) -> bool:
        """Check if notification has been read."""
        return self.read_at is not None

    @property
    def is_archived(self) -> bool:
        """Check if notification has been archived."""
        return self.archived_at is not None

    def mark_read(self) -> None:
        """Mark notification as read."""
        if self.read_at is None:
            self.read_at = datetime.now(timezone.utc)
            self.status = NotificationStatus.READ

    def mark_archived(self) -> None:
        """Mark notification as archived."""
        if self.archived_at is None:
            self.archived_at = datetime.now(timezone.utc)
            self.status = NotificationStatus.ARCHIVED

    def mark_sent(self, channel: NotificationChannel) -> None:
        """Mark notification as sent via a specific channel."""
        if channel == NotificationChannel.EMAIL:
            self.email_sent = True
        elif channel == NotificationChannel.WEBSOCKET:
            self.websocket_sent = True

        if self.status == NotificationStatus.PENDING:
            self.status = NotificationStatus.SENT

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "notification_type": self.notification_type.value,
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "action_url": self.action_url,
            "priority": self.priority.value,
            "status": self.status.value,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }


@dataclass
class NotificationPreference:
    """User preferences for notifications.

    Controls which notifications a user wants to receive
    and through which channels.
    """

    # Identity
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)

    # Category-level preferences
    category: NotificationCategory = NotificationCategory.SYSTEM

    # Channel preferences for this category
    in_app_enabled: bool = True
    email_enabled: bool = True
    push_enabled: bool = False  # Future

    # Specific notification type overrides (optional)
    # If a type is in disabled_types, it won't be sent even if category is enabled
    disabled_types: list[str] = field(default_factory=list)

    # Email preferences
    email_digest: bool = False  # Batch emails into digest
    email_frequency: str = "immediate"  # immediate, daily, weekly

    def is_channel_enabled(self, channel: NotificationChannel) -> bool:
        """Check if a channel is enabled for this category."""
        if channel == NotificationChannel.IN_APP:
            return self.in_app_enabled
        elif channel == NotificationChannel.EMAIL:
            return self.email_enabled
        elif channel == NotificationChannel.PUSH:
            return self.push_enabled
        elif channel == NotificationChannel.WEBSOCKET:
            return self.in_app_enabled  # WebSocket follows in-app
        return False

    def is_type_enabled(self, notification_type: NotificationType) -> bool:
        """Check if a specific notification type is enabled."""
        return notification_type.value not in self.disabled_types


@dataclass
class NotificationTemplate:
    """Template for generating notification content.

    Provides consistent formatting for notification messages.
    """

    notification_type: NotificationType
    title_template: str
    message_template: str
    default_action_url: str | None = None

    def render(self, context: dict[str, Any]) -> tuple[str, str]:
        """Render the template with context.

        Args:
            context: Variables to substitute in templates.

        Returns:
            Tuple of (title, message).
        """
        title = self.title_template.format(**context)
        message = self.message_template.format(**context)
        return title, message


# Default templates for common notification types
NOTIFICATION_TEMPLATES: dict[NotificationType, NotificationTemplate] = {
    # Finance notifications
    NotificationType.FINANCE_TRANSACTION_CREATED: NotificationTemplate(
        notification_type=NotificationType.FINANCE_TRANSACTION_CREATED,
        title_template="Transaction Recorded",
        message_template="A {transaction_type} of {amount} was recorded in {account_name}.",
        default_action_url="/transactions/{transaction_id}/",
    ),
    NotificationType.FINANCE_LOW_BALANCE: NotificationTemplate(
        notification_type=NotificationType.FINANCE_LOW_BALANCE,
        title_template="Low Balance Alert",
        message_template="Your {account_name} balance is {balance}. Consider adding funds.",
        default_action_url="/accounts/{account_id}/",
    ),
    NotificationType.FINANCE_TRANSFER_COMPLETED: NotificationTemplate(
        notification_type=NotificationType.FINANCE_TRANSFER_COMPLETED,
        title_template="Transfer Completed",
        message_template="Transfer of {amount} from {from_account} to {to_account} completed.",
    ),
    # Social notifications
    NotificationType.SOCIAL_DEBT_CREATED: NotificationTemplate(
        notification_type=NotificationType.SOCIAL_DEBT_CREATED,
        title_template="New Debt Recorded",
        message_template="{contact_name} {direction} you {amount}.",
        default_action_url="/debts/{debt_id}/",
    ),
    NotificationType.SOCIAL_DEBT_SETTLED: NotificationTemplate(
        notification_type=NotificationType.SOCIAL_DEBT_SETTLED,
        title_template="Debt Settled",
        message_template="Debt of {amount} with {contact_name} has been settled.",
    ),
    NotificationType.SOCIAL_EXPENSE_ADDED: NotificationTemplate(
        notification_type=NotificationType.SOCIAL_EXPENSE_ADDED,
        title_template="New Group Expense",
        message_template="{payer_name} added '{description}' ({amount}) to {group_name}. Your share: {share_amount}.",
        default_action_url="/groups/{group_id}/",
    ),
    NotificationType.SOCIAL_SETTLEMENT_RECEIVED: NotificationTemplate(
        notification_type=NotificationType.SOCIAL_SETTLEMENT_RECEIVED,
        title_template="Payment Received",
        message_template="{contact_name} paid you {amount}.",
    ),
}
