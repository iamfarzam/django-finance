"""Domain services for notifications."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from modules.notifications.domain.entities import (
    Notification,
    NotificationPreference,
    NotificationTemplate,
    NOTIFICATION_TEMPLATES,
)
from modules.notifications.domain.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)


class NotificationRepository(Protocol):
    """Repository interface for notifications."""

    def save(self, notification: Notification) -> Notification:
        """Save a notification."""
        ...

    def get_by_id(self, notification_id: UUID) -> Notification | None:
        """Get notification by ID."""
        ...

    def get_for_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a user."""
        ...

    def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read."""
        ...

    def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a user."""
        ...


class PreferenceRepository(Protocol):
    """Repository interface for notification preferences."""

    def get_for_user(self, user_id: UUID) -> list[NotificationPreference]:
        """Get all preferences for a user."""
        ...

    def get_for_category(
        self,
        user_id: UUID,
        category: NotificationCategory,
    ) -> NotificationPreference | None:
        """Get preference for a specific category."""
        ...

    def save(self, preference: NotificationPreference) -> NotificationPreference:
        """Save a preference."""
        ...


class NotificationDispatcher(Protocol):
    """Interface for dispatching notifications to channels."""

    def dispatch_in_app(self, notification: Notification) -> bool:
        """Send notification to in-app channel (database + WebSocket)."""
        ...

    def dispatch_email(self, notification: Notification) -> bool:
        """Send notification via email."""
        ...

    def dispatch_websocket(self, notification: Notification) -> bool:
        """Send notification via WebSocket."""
        ...


class NotificationService:
    """Domain service for creating and managing notifications."""

    def __init__(
        self,
        notification_repo: NotificationRepository,
        preference_repo: PreferenceRepository,
        dispatcher: NotificationDispatcher,
    ):
        self._notification_repo = notification_repo
        self._preference_repo = preference_repo
        self._dispatcher = dispatcher

    def create_notification(
        self,
        user_id: UUID,
        tenant_id: UUID,
        notification_type: NotificationType,
        title: str | None = None,
        message: str | None = None,
        data: dict[str, Any] | None = None,
        action_url: str | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: list[NotificationChannel] | None = None,
    ) -> Notification:
        """Create and dispatch a notification.

        Args:
            user_id: Target user ID.
            tenant_id: Tenant context.
            notification_type: Type of notification.
            title: Custom title (uses template if not provided).
            message: Custom message (uses template if not provided).
            data: Additional data for the notification.
            action_url: URL for action button.
            priority: Notification priority.
            channels: Specific channels to use (uses preferences if not provided).

        Returns:
            Created notification.
        """
        data = data or {}

        # Use template if title/message not provided
        if title is None or message is None:
            template = NOTIFICATION_TEMPLATES.get(notification_type)
            if template:
                try:
                    t_title, t_message = template.render(data)
                    title = title or t_title
                    message = message or t_message
                    if action_url is None and template.default_action_url:
                        action_url = template.default_action_url.format(**data)
                except KeyError:
                    # Template variables missing, use defaults
                    title = title or notification_type.value
                    message = message or ""

        # Determine channels based on user preferences
        if channels is None:
            channels = self._get_enabled_channels(user_id, notification_type)

        # Create notification
        notification = Notification(
            user_id=user_id,
            tenant_id=tenant_id,
            notification_type=notification_type,
            title=title or notification_type.value,
            message=message or "",
            data=data,
            action_url=action_url,
            priority=priority,
            channels=channels,
        )

        # Save to database (always, for audit trail)
        notification = self._notification_repo.save(notification)

        # Dispatch to channels
        self._dispatch_notification(notification)

        return notification

    def _get_enabled_channels(
        self,
        user_id: UUID,
        notification_type: NotificationType,
    ) -> list[NotificationChannel]:
        """Get enabled channels for a notification type based on user preferences."""
        category = notification_type.category
        preference = self._preference_repo.get_for_category(user_id, category)

        if preference is None:
            # Default: in-app and WebSocket enabled
            return [NotificationChannel.IN_APP, NotificationChannel.WEBSOCKET]

        # Check if this specific type is disabled
        if not preference.is_type_enabled(notification_type):
            return []

        channels = []
        if preference.in_app_enabled:
            channels.append(NotificationChannel.IN_APP)
            channels.append(NotificationChannel.WEBSOCKET)
        if preference.email_enabled:
            channels.append(NotificationChannel.EMAIL)

        return channels

    def _dispatch_notification(self, notification: Notification) -> None:
        """Dispatch notification to all enabled channels."""
        for channel in notification.channels:
            try:
                if channel == NotificationChannel.IN_APP:
                    self._dispatcher.dispatch_in_app(notification)
                elif channel == NotificationChannel.EMAIL:
                    self._dispatcher.dispatch_email(notification)
                elif channel == NotificationChannel.WEBSOCKET:
                    self._dispatcher.dispatch_websocket(notification)
            except Exception:
                # Log error but don't fail the whole notification
                pass

    def get_notifications(
        self,
        user_id: UUID,
        unread_only: bool = False,
        limit: int = 50,
    ) -> list[Notification]:
        """Get notifications for a user."""
        return self._notification_repo.get_for_user(user_id, unread_only, limit)

    def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read."""
        return self._notification_repo.mark_read(notification_id, user_id)

    def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read."""
        return self._notification_repo.mark_all_read(user_id)

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications."""
        notifications = self._notification_repo.get_for_user(user_id, unread_only=True)
        return len(notifications)


def get_default_preferences(user_id: UUID, tenant_id: UUID) -> list[NotificationPreference]:
    """Generate default notification preferences for a new user."""
    preferences = []

    for category in NotificationCategory:
        preference = NotificationPreference(
            user_id=user_id,
            tenant_id=tenant_id,
            category=category,
            in_app_enabled=True,
            email_enabled=category in [
                NotificationCategory.ACCOUNT,
                NotificationCategory.SOCIAL,
            ],
            push_enabled=False,
        )
        preferences.append(preference)

    return preferences
