"""Domain layer for notifications module."""

from modules.notifications.domain.enums import (
    NotificationCategory,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
)
from modules.notifications.domain.entities import (
    Notification,
    NotificationPreference,
)
from modules.notifications.domain.services import NotificationService

__all__ = [
    "NotificationCategory",
    "NotificationChannel",
    "NotificationPriority",
    "NotificationType",
    "Notification",
    "NotificationPreference",
    "NotificationService",
]
