"""Django ORM models for the subscriptions module.

Models:
- SubscriptionTier: Admin-managed tier definitions
- Subscription: Per-user subscription record
- UsageRecord: Usage tracking for limits
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.db import models
from django.utils import timezone

from shared.models import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class SubscriptionTier(BaseModel):
    """Subscription tier definition.

    Defines the features, limits, and pricing for a subscription tier.
    Managed by administrators.
    """

    class Meta:
        db_table = "subscription_tiers"
        ordering = ["display_order", "name"]
        verbose_name = "Subscription Tier"
        verbose_name_plural = "Subscription Tiers"

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Unique code for the tier (e.g., 'free', 'premium').",
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name for the tier.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Description of the tier for marketing.",
    )

    # Limits - empty dict means unlimited
    limits = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            "Usage limits as JSON. Keys: accounts_max, transactions_monthly, "
            "contacts_max, expense_groups_max, api_calls_daily. "
            "Empty or 0 means unlimited."
        ),
    )

    # Features - list of feature codes
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of feature codes enabled for this tier.",
    )

    # Pricing
    price_monthly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monthly price in USD.",
    )
    price_yearly = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Yearly price in USD.",
    )

    # Display
    display_order = models.PositiveIntegerField(
        default=0,
        help_text="Order for displaying tiers.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this tier is available for new subscriptions.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default tier for new users.",
    )

    # Stripe integration
    stripe_price_id_monthly = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Stripe Price ID for monthly billing.",
    )
    stripe_price_id_yearly = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Stripe Price ID for yearly billing.",
    )

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"

    def has_feature(self, feature_code: str) -> bool:
        """Check if the tier includes a feature.

        Args:
            feature_code: The feature code to check.

        Returns:
            True if the tier includes the feature.
        """
        return feature_code in (self.features or [])

    def get_limit(self, limit_key: str) -> int | None:
        """Get a limit value for the tier.

        Args:
            limit_key: The limit key.

        Returns:
            The limit value, or None if unlimited.
        """
        limits = self.limits or {}
        return limits.get(limit_key)


class Subscription(BaseModel):
    """User subscription record.

    Tracks a user's subscription to a tier, including billing period
    and external payment provider references.
    """

    class Status(models.TextChoices):
        """Subscription status values."""

        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past Due"
        CANCELED = "canceled", "Canceled"
        EXPIRED = "expired", "Expired"
        INCOMPLETE = "incomplete", "Incomplete"

    class BillingCycle(models.TextChoices):
        """Billing cycle options."""

        MONTHLY = "monthly", "Monthly"
        YEARLY = "yearly", "Yearly"

    class Meta:
        db_table = "subscriptions"
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
        help_text="The user this subscription belongs to.",
    )
    tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        help_text="The subscription tier.",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        help_text="Current subscription status.",
    )

    # Billing period
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.MONTHLY,
        help_text="Billing cycle (monthly or yearly).",
    )
    current_period_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Start of the current billing period.",
    )
    current_period_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="End of the current billing period.",
    )

    # Trial
    trial_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the trial started.",
    )
    trial_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the trial ends.",
    )

    # Cancellation
    canceled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the subscription was canceled.",
    )
    cancel_at_period_end = models.BooleanField(
        default=False,
        help_text="Whether to cancel at the end of the current period.",
    )

    # Payment provider (Stripe-ready)
    payment_provider = models.CharField(
        max_length=50,
        default="stripe",
        help_text="Payment provider name.",
    )
    external_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="External subscription ID (e.g., Stripe subscription ID).",
    )
    external_customer_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="External customer ID (e.g., Stripe customer ID).",
    )

    def __str__(self) -> str:
        return f"{self.user.email} - {self.tier.name} ({self.status})"

    def is_active(self) -> bool:
        """Check if the subscription is active.

        Returns:
            True if the subscription is active or in trial.
        """
        if self.status not in (self.Status.ACTIVE, self.Status.TRIAL):
            return False

        # Check if expired
        if self.current_period_end and self.current_period_end < timezone.now():
            return False

        return True

    def is_premium(self) -> bool:
        """Check if this is a premium subscription.

        Returns:
            True if the tier is not 'free'.
        """
        return self.tier.code != "free"

    def days_until_expiry(self) -> int | None:
        """Calculate days until subscription expires.

        Returns:
            Number of days until expiry, or None if no expiry date.
        """
        if not self.current_period_end:
            return None

        delta = self.current_period_end - timezone.now()
        return max(0, delta.days)

    def has_feature(self, feature_code: str) -> bool:
        """Check if the subscription includes a feature.

        Args:
            feature_code: The feature code to check.

        Returns:
            True if the subscription includes the feature.
        """
        if not self.is_active():
            return False
        return self.tier.has_feature(feature_code)


class UsageRecord(BaseModel):
    """Usage tracking record for rate limiting.

    Tracks usage counts for periodic limits (monthly transactions,
    daily API calls, etc.).
    """

    class Meta:
        db_table = "usage_records"
        ordering = ["-period_start"]
        verbose_name = "Usage Record"
        verbose_name_plural = "Usage Records"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "usage_type", "period_start"],
                name="unique_usage_per_user_type_period",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "usage_type", "period_start"]),
        ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_records",
        help_text="The user this usage record belongs to.",
    )
    usage_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Type of usage being tracked.",
    )
    count = models.PositiveIntegerField(
        default=0,
        help_text="Usage count for the period.",
    )
    period_start = models.DateField(
        help_text="Start of the tracking period.",
    )
    period_end = models.DateField(
        null=True,
        blank=True,
        help_text="End of the tracking period.",
    )

    def __str__(self) -> str:
        return f"{self.user.email} - {self.usage_type}: {self.count} ({self.period_start})"
