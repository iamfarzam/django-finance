"""DRF serializers for notifications."""

from __future__ import annotations

from rest_framework import serializers

from modules.notifications.infrastructure.models import (
    Notification,
    NotificationPreference,
)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    is_read = serializers.BooleanField(read_only=True)
    is_archived = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "category",
            "title",
            "message",
            "data",
            "action_url",
            "priority",
            "status",
            "is_read",
            "is_archived",
            "created_at",
            "read_at",
        ]
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences."""

    class Meta:
        model = NotificationPreference
        fields = [
            "id",
            "category",
            "in_app_enabled",
            "email_enabled",
            "push_enabled",
            "email_frequency",
            "disabled_types",
        ]
        read_only_fields = ["id", "category"]


class UpdatePreferenceSerializer(serializers.Serializer):
    """Serializer for updating preferences."""

    in_app_enabled = serializers.BooleanField(required=False)
    email_enabled = serializers.BooleanField(required=False)
    push_enabled = serializers.BooleanField(required=False)
    email_frequency = serializers.ChoiceField(
        choices=NotificationPreference.EmailFrequency.choices,
        required=False,
    )
    disabled_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
    )


class MarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read.",
    )
