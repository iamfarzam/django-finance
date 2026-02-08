"""Django admin configuration for notifications."""

from django.contrib import admin
from django.utils.html import format_html

from modules.notifications.infrastructure.models import (
    Notification,
    NotificationPreference,
)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for notifications."""

    list_display = [
        "title",
        "user_id",
        "notification_type_badge",
        "category_badge",
        "priority_badge",
        "status_badge",
        "is_read",
        "created_at",
    ]
    list_filter = [
        "category",
        "notification_type",
        "priority",
        "status",
        "email_sent",
        "websocket_sent",
        "created_at",
    ]
    search_fields = ["title", "message", "user_id"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "read_at",
        "archived_at",
        "email_sent_at",
        "websocket_sent_at",
    ]
    ordering = ["-created_at"]

    fieldsets = [
        (
            "Recipient",
            {
                "fields": ["user_id", "tenant_id"],
            },
        ),
        (
            "Content",
            {
                "fields": [
                    "notification_type",
                    "category",
                    "title",
                    "message",
                    "data",
                    "action_url",
                ],
            },
        ),
        (
            "Delivery",
            {
                "fields": [
                    "priority",
                    "status",
                    "email_sent",
                    "email_sent_at",
                    "websocket_sent",
                    "websocket_sent_at",
                ],
            },
        ),
        (
            "Timestamps",
            {
                "fields": [
                    "id",
                    "created_at",
                    "updated_at",
                    "read_at",
                    "archived_at",
                ],
                "classes": ["collapse"],
            },
        ),
    ]

    def notification_type_badge(self, obj):
        """Display notification type as badge."""
        return format_html(
            '<span style="padding: 2px 8px; border-radius: 4px; '
            'background-color: #e0e0e0; font-size: 11px;">{}</span>',
            obj.notification_type.split(".")[-1],
        )

    notification_type_badge.short_description = "Type"

    def category_badge(self, obj):
        """Display category with color."""
        colors = {
            "account": "#2196F3",
            "finance": "#4CAF50",
            "social": "#9C27B0",
            "system": "#FF9800",
        }
        color = colors.get(obj.category, "#757575")
        return format_html(
            '<span style="padding: 2px 8px; border-radius: 4px; '
            'background-color: {}; color: white; font-size: 11px;">{}</span>',
            color,
            obj.category.upper(),
        )

    category_badge.short_description = "Category"

    def priority_badge(self, obj):
        """Display priority with color."""
        colors = {
            "low": "#9E9E9E",
            "normal": "#2196F3",
            "high": "#FF9800",
            "urgent": "#F44336",
        }
        color = colors.get(obj.priority, "#757575")
        return format_html(
            '<span style="padding: 2px 8px; border-radius: 4px; '
            'background-color: {}; color: white; font-size: 11px;">{}</span>',
            color,
            obj.priority.upper(),
        )

    priority_badge.short_description = "Priority"

    def status_badge(self, obj):
        """Display status with color."""
        colors = {
            "pending": "#FF9800",
            "sent": "#2196F3",
            "read": "#4CAF50",
            "archived": "#9E9E9E",
            "failed": "#F44336",
        }
        color = colors.get(obj.status, "#757575")
        return format_html(
            '<span style="padding: 2px 8px; border-radius: 4px; '
            'background-color: {}; color: white; font-size: 11px;">{}</span>',
            color,
            obj.status.upper(),
        )

    status_badge.short_description = "Status"

    def is_read(self, obj):
        """Display read status."""
        return obj.read_at is not None

    is_read.boolean = True
    is_read.short_description = "Read"


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin for notification preferences."""

    list_display = [
        "user_id",
        "category",
        "in_app_enabled",
        "email_enabled",
        "email_frequency",
        "push_enabled",
    ]
    list_filter = ["category", "in_app_enabled", "email_enabled", "email_frequency"]
    search_fields = ["user_id"]
    ordering = ["user_id", "category"]

    fieldsets = [
        (
            "User",
            {
                "fields": ["user_id", "tenant_id", "category"],
            },
        ),
        (
            "Channel Settings",
            {
                "fields": [
                    "in_app_enabled",
                    "email_enabled",
                    "push_enabled",
                    "email_frequency",
                ],
            },
        ),
        (
            "Disabled Types",
            {
                "fields": ["disabled_types"],
                "classes": ["collapse"],
            },
        ),
    ]
