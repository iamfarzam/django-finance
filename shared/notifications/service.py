"""Notification service for sending real-time updates."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from shared.notifications.types import NotificationChannel, NotificationType

logger = logging.getLogger(__name__)


@dataclass
class NotificationPayload:
    """Payload for a notification message."""

    notification_type: NotificationType
    title: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    action_url: str | None = None
    notification_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "notification_id": str(self.notification_id),
            "notification_type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "action_url": self.action_url,
            "timestamp": self.timestamp.isoformat(),
        }


class NotificationService:
    """Service for sending notifications via WebSocket channels."""

    def __init__(self):
        self._channel_layer = None

    @property
    def channel_layer(self):
        """Get the channel layer lazily."""
        if self._channel_layer is None:
            self._channel_layer = get_channel_layer()
        return self._channel_layer

    def send_to_user(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
        action_url: str | None = None,
    ) -> None:
        """Send a notification to a specific user.

        Args:
            user_id: The user's ID.
            notification_type: Type of notification.
            title: Notification title.
            message: Notification message.
            data: Additional data to include.
            action_url: Optional URL for action.
        """
        payload = NotificationPayload(
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
        )

        channel_name = NotificationChannel.USER_NOTIFICATIONS.format(user_id=user_id)
        self._send_to_group(channel_name, "notification.message", payload)

    def send_finance_update(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send a finance-related update to a user.

        Args:
            user_id: The user's ID.
            notification_type: Type of notification.
            title: Notification title.
            message: Notification message.
            data: Additional data (e.g., account_id, new_balance).
        """
        payload = NotificationPayload(
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
        )

        channel_name = NotificationChannel.FINANCE_UPDATES.format(user_id=user_id)
        self._send_to_group(channel_name, "finance.update", payload)

        # Also send to general notifications
        self.send_to_user(user_id, notification_type, title, message, data)

    def send_social_update(
        self,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send a social finance update to a user.

        Args:
            user_id: The user's ID.
            notification_type: Type of notification.
            title: Notification title.
            message: Notification message.
            data: Additional data (e.g., contact_id, debt_id).
        """
        payload = NotificationPayload(
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
        )

        channel_name = NotificationChannel.SOCIAL_UPDATES.format(user_id=user_id)
        self._send_to_group(channel_name, "social.update", payload)

        # Also send to general notifications
        self.send_to_user(user_id, notification_type, title, message, data)

    def send_account_update(
        self,
        account_id: UUID,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send an update for a specific account.

        Args:
            account_id: The account's ID.
            user_id: The account owner's user ID.
            notification_type: Type of notification.
            title: Notification title.
            message: Notification message.
            data: Additional data.
        """
        payload = NotificationPayload(
            notification_type=notification_type,
            title=title,
            message=message,
            data={**(data or {}), "account_id": str(account_id)},
        )

        # Send to account-specific channel
        channel_name = NotificationChannel.ACCOUNT_UPDATES.format(account_id=account_id)
        self._send_to_group(channel_name, "account.update", payload)

        # Also send to user's finance channel
        self.send_finance_update(user_id, notification_type, title, message, payload.data)

    def send_expense_group_update(
        self,
        group_id: UUID,
        member_user_ids: list[UUID],
        notification_type: NotificationType,
        title: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send an update to all members of an expense group.

        Args:
            group_id: The expense group's ID.
            member_user_ids: List of member user IDs (those with linked accounts).
            notification_type: Type of notification.
            title: Notification title.
            message: Notification message.
            data: Additional data.
        """
        payload = NotificationPayload(
            notification_type=notification_type,
            title=title,
            message=message,
            data={**(data or {}), "group_id": str(group_id)},
        )

        # Send to group-specific channel
        channel_name = NotificationChannel.EXPENSE_GROUP_UPDATES.format(group_id=group_id)
        self._send_to_group(channel_name, "expense_group.update", payload)

        # Also send to each member's social channel
        for user_id in member_user_ids:
            self.send_social_update(user_id, notification_type, title, message, payload.data)

    def send_system_status(
        self,
        status: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Send a system-wide status update.

        Args:
            status: Status indicator (e.g., "ok", "degraded", "maintenance").
            message: Status message.
            data: Additional data.
        """
        payload = NotificationPayload(
            notification_type=NotificationType.INFO,
            title="System Status",
            message=message,
            data={**(data or {}), "status": status},
        )

        self._send_to_group(
            NotificationChannel.SYSTEM_STATUS.value,
            "status.update",
            payload,
        )

    def _send_to_group(
        self,
        group_name: str,
        message_type: str,
        payload: NotificationPayload,
    ) -> None:
        """Send a message to a channel group.

        Args:
            group_name: The channel group name.
            message_type: The message type for the consumer.
            payload: The notification payload.
        """
        try:
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    "type": message_type,
                    **payload.to_dict(),
                },
            )
            logger.debug(
                "Sent notification to group",
                extra={
                    "group": group_name,
                    "message_type": message_type,
                    "notification_id": str(payload.notification_id),
                },
            )
        except Exception as e:
            logger.error(
                "Failed to send notification",
                extra={
                    "group": group_name,
                    "message_type": message_type,
                    "error": str(e),
                },
                exc_info=True,
            )


# Singleton instance
notification_service = NotificationService()
