"""Repository implementations for notifications."""

from __future__ import annotations

from uuid import UUID

from django.utils import timezone

from modules.notifications.infrastructure.models import (
    Notification as NotificationModel,
    NotificationPreference as PreferenceModel,
)


class NotificationRepository:
    """Django ORM implementation of notification repository."""

    def save(self, notification_data: dict) -> NotificationModel:
        """Save a notification."""
        return NotificationModel.objects.create(**notification_data)

    def get_by_id(self, notification_id: UUID) -> NotificationModel | None:
        """Get notification by ID."""
        try:
            return NotificationModel.objects.get(id=notification_id)
        except NotificationModel.DoesNotExist:
            return None

    def get_for_user(
        self,
        user_id: UUID,
        unread_only: bool = False,
        category: str | None = None,
        limit: int = 50,
    ) -> list[NotificationModel]:
        """Get notifications for a user."""
        queryset = NotificationModel.objects.filter(user_id=user_id)

        if unread_only:
            queryset = queryset.filter(read_at__isnull=True)

        if category:
            queryset = queryset.filter(category=category)

        # Exclude archived
        queryset = queryset.exclude(status=NotificationModel.Status.ARCHIVED)

        return list(queryset.order_by("-created_at")[:limit])

    def mark_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read."""
        try:
            notification = NotificationModel.objects.get(
                id=notification_id,
                user_id=user_id,
            )
            notification.mark_read()
            return True
        except NotificationModel.DoesNotExist:
            return False

    def mark_all_read(self, user_id: UUID, category: str | None = None) -> int:
        """Mark all notifications as read for a user."""
        queryset = NotificationModel.objects.filter(
            user_id=user_id,
            read_at__isnull=True,
        )

        if category:
            queryset = queryset.filter(category=category)

        return queryset.update(
            read_at=timezone.now(),
            status=NotificationModel.Status.READ,
            updated_at=timezone.now(),
        )

    def get_unread_count(self, user_id: UUID) -> int:
        """Get count of unread notifications."""
        return NotificationModel.objects.filter(
            user_id=user_id,
            read_at__isnull=True,
        ).exclude(
            status=NotificationModel.Status.ARCHIVED,
        ).count()

    def archive(self, notification_id: UUID, user_id: UUID) -> bool:
        """Archive a notification."""
        try:
            notification = NotificationModel.objects.get(
                id=notification_id,
                user_id=user_id,
            )
            notification.mark_archived()
            return True
        except NotificationModel.DoesNotExist:
            return False


class PreferenceRepository:
    """Django ORM implementation of preference repository."""

    def get_for_user(self, user_id: UUID, tenant_id: UUID) -> list[PreferenceModel]:
        """Get all preferences for a user, creating defaults if needed."""
        return PreferenceModel.get_or_create_defaults(user_id, tenant_id)

    def get_for_category(
        self,
        user_id: UUID,
        category: str,
    ) -> PreferenceModel | None:
        """Get preference for a specific category."""
        try:
            return PreferenceModel.objects.get(
                user_id=user_id,
                category=category,
            )
        except PreferenceModel.DoesNotExist:
            return None

    def save(self, preference: PreferenceModel) -> PreferenceModel:
        """Save a preference."""
        preference.save()
        return preference

    def update(
        self,
        user_id: UUID,
        category: str,
        updates: dict,
    ) -> PreferenceModel | None:
        """Update preferences for a category."""
        try:
            preference = PreferenceModel.objects.get(
                user_id=user_id,
                category=category,
            )
            for key, value in updates.items():
                setattr(preference, key, value)
            preference.save()
            return preference
        except PreferenceModel.DoesNotExist:
            return None
