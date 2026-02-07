"""Django admin configuration for subscriptions module."""

from django.contrib import admin
from django.utils.html import format_html

from modules.subscriptions.infrastructure.models import (
    Subscription,
    SubscriptionTier,
    UsageRecord,
)


@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    """Admin for SubscriptionTier model."""

    list_display = [
        "name",
        "code",
        "price_monthly",
        "price_yearly",
        "is_active",
        "is_default",
        "display_order",
    ]
    list_filter = ["is_active", "is_default"]
    search_fields = ["name", "code"]
    ordering = ["display_order", "name"]

    readonly_fields = ["id", "created_at", "updated_at"]

    fieldsets = [
        (
            None,
            {
                "fields": ["code", "name", "description"],
            },
        ),
        (
            "Pricing",
            {
                "fields": ["price_monthly", "price_yearly"],
            },
        ),
        (
            "Features & Limits",
            {
                "fields": ["features", "limits"],
                "description": (
                    "Features: List of feature codes (e.g., ['reports.advanced', 'export.pdf']). "
                    "Limits: JSON object with limit keys (e.g., {'accounts_max': 3}). "
                    "Empty limits means unlimited."
                ),
            },
        ),
        (
            "Display",
            {
                "fields": ["display_order", "is_active", "is_default"],
            },
        ),
        (
            "Stripe Integration",
            {
                "fields": ["stripe_price_id_monthly", "stripe_price_id_yearly"],
                "classes": ["collapse"],
            },
        ),
        (
            "Metadata",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin for Subscription model."""

    list_display = [
        "user_email",
        "tier",
        "status",
        "billing_cycle",
        "current_period_end",
        "is_active_display",
    ]
    list_filter = ["status", "tier", "billing_cycle"]
    search_fields = ["user__email", "external_id", "external_customer_id"]
    raw_id_fields = ["user"]
    ordering = ["-created_at"]

    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "is_active_display",
        "days_until_expiry_display",
    ]

    fieldsets = [
        (
            None,
            {
                "fields": ["user", "tier", "status", "billing_cycle"],
            },
        ),
        (
            "Billing Period",
            {
                "fields": ["current_period_start", "current_period_end"],
            },
        ),
        (
            "Trial",
            {
                "fields": ["trial_start", "trial_end"],
                "classes": ["collapse"],
            },
        ),
        (
            "Cancellation",
            {
                "fields": ["canceled_at", "cancel_at_period_end"],
                "classes": ["collapse"],
            },
        ),
        (
            "Payment Provider",
            {
                "fields": [
                    "payment_provider",
                    "external_id",
                    "external_customer_id",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Status",
            {
                "fields": [
                    "is_active_display",
                    "days_until_expiry_display",
                ],
            },
        ),
        (
            "Metadata",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email

    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"

    def is_active_display(self, obj):
        """Display active status with color."""
        if obj.is_active():
            return format_html(
                '<span style="color: green; font-weight: bold;">Active</span>'
            )
        return format_html('<span style="color: red;">Inactive</span>')

    is_active_display.short_description = "Active"

    def days_until_expiry_display(self, obj):
        """Display days until expiry."""
        days = obj.days_until_expiry()
        if days is None:
            return "N/A"
        if days <= 0:
            return format_html('<span style="color: red;">Expired</span>')
        if days <= 7:
            return format_html(
                '<span style="color: orange;">{} days</span>', days
            )
        return f"{days} days"

    days_until_expiry_display.short_description = "Days Until Expiry"


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    """Admin for UsageRecord model."""

    list_display = [
        "user_email",
        "usage_type",
        "count",
        "period_start",
        "period_end",
    ]
    list_filter = ["usage_type", "period_start"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]
    ordering = ["-period_start", "-created_at"]

    readonly_fields = ["id", "created_at", "updated_at"]

    def user_email(self, obj):
        """Display user email."""
        return obj.user.email

    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"
