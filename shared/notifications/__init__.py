"""Shared notification services for real-time updates.

This module provides a unified notification system that integrates
with Django Channels for real-time WebSocket updates.
"""

from shared.notifications.service import NotificationService
from shared.notifications.types import NotificationType, NotificationChannel

__all__ = [
    "NotificationService",
    "NotificationType",
    "NotificationChannel",
]
