"""Django models for notifications."""

from __future__ import annotations

from django.db import models
from django.utils import timezone

from shared.models import TenantModel


class Notification(TenantModel):
    """Notification stored in the database.

    Represents an in-app notification that can be viewed,
    marked as read, and archived by the user.
    """

    class NotificationType(models.TextChoices):
        """Notification type choices."""

        # Account
        ACCOUNT_WELCOME = "account.welcome", "Welcome"
        ACCOUNT_EMAIL_VERIFIED = "account.email_verified", "Email Verified"
        ACCOUNT_PASSWORD_CHANGED = "account.password_changed", "Password Changed"
        ACCOUNT_PASSWORD_RESET = "account.password_reset", "Password Reset"
        ACCOUNT_LOGIN_NEW_DEVICE = "account.login_new_device", "New Device Login"
        ACCOUNT_SUBSCRIPTION_CHANGED = "account.subscription_changed", "Subscription Changed"

        # Finance
        FINANCE_TRANSACTION_CREATED = "finance.transaction_created", "Transaction Created"
        FINANCE_TRANSACTION_POSTED = "finance.transaction_posted", "Transaction Posted"
        FINANCE_LARGE_TRANSACTION = "finance.large_transaction", "Large Transaction"
        FINANCE_LOW_BALANCE = "finance.low_balance", "Low Balance"
        FINANCE_TRANSFER_COMPLETED = "finance.transfer_completed", "Transfer Completed"
        FINANCE_ACCOUNT_CREATED = "finance.account_created", "Account Created"
        FINANCE_ACCOUNT_CLOSED = "finance.account_closed", "Account Closed"
        FINANCE_NET_WORTH_MILESTONE = "finance.net_worth_milestone", "Net Worth Milestone"

        # Social
        SOCIAL_DEBT_CREATED = "social.debt_created", "Debt Created"
        SOCIAL_DEBT_REMINDER = "social.debt_reminder", "Debt Reminder"
        SOCIAL_DEBT_SETTLED = "social.debt_settled", "Debt Settled"
        SOCIAL_SETTLEMENT_RECEIVED = "social.settlement_received", "Settlement Received"
        SOCIAL_EXPENSE_ADDED = "social.expense_added", "Expense Added"
        SOCIAL_GROUP_INVITATION = "social.group_invitation", "Group Invitation"
        SOCIAL_GROUP_EXPENSE_SPLIT = "social.group_expense_split", "Expense Split"
        SOCIAL_BALANCE_UPDATED = "social.balance_updated", "Balance Updated"

        # System
        SYSTEM_ANNOUNCEMENT = "system.announcement", "Announcement"
        SYSTEM_MAINTENANCE = "system.maintenance", "Maintenance"
        SYSTEM_FEATURE_UPDATE = "system.feature_update", "Feature Update"

    class Category(models.TextChoices):
        """Notification category choices."""

        ACCOUNT = "account", "Account"
        FINANCE = "finance", "Finance"
        SOCIAL = "social", "Social"
        SYSTEM = "system", "System"

    class Priority(models.TextChoices):
        """Notification priority choices."""

        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        """Notification status choices."""

        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        READ = "read", "Read"
        ARCHIVED = "archived", "Archived"
        FAILED = "failed", "Failed"

    # Recipient
    user_id = models.UUIDField(
        db_index=True,
        help_text="User to notify.",
    )

    # Content
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True,
        help_text="Type of notification.",
    )
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        db_index=True,
        help_text="Category for grouping.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title.",
    )
    message = models.TextField(
        help_text="Notification message.",
    )
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data.",
    )
    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional action URL.",
    )

    # Delivery
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Channel tracking
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    websocket_sent = models.BooleanField(default=False)
    websocket_sent_at = models.DateTimeField(null=True, blank=True)

    # Status timestamps
    read_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications"
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user_id", "status", "-created_at"],
                name="idx_notif_user_status",
            ),
            models.Index(
                fields=["user_id", "category", "-created_at"],
                name="idx_notif_user_category",
            ),
            models.Index(
                fields=["tenant_id", "notification_type"],
                name="idx_notif_tenant_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.notification_type})"

    def save(self, *args, **kwargs):
        """Set category from notification type if not set."""
        if not self.category:
            self.category = self.notification_type.split(".")[0]
        super().save(*args, **kwargs)

    def mark_read(self) -> None:
        """Mark notification as read."""
        if self.read_at is None:
            self.read_at = timezone.now()
            self.status = self.Status.READ
            self.save(update_fields=["read_at", "status", "updated_at"])

    def mark_archived(self) -> None:
        """Mark notification as archived."""
        if self.archived_at is None:
            self.archived_at = timezone.now()
            self.status = self.Status.ARCHIVED
            self.save(update_fields=["archived_at", "status", "updated_at"])

    def mark_email_sent(self) -> None:
        """Mark email as sent."""
        self.email_sent = True
        self.email_sent_at = timezone.now()
        if self.status == self.Status.PENDING:
            self.status = self.Status.SENT
        self.save(update_fields=["email_sent", "email_sent_at", "status", "updated_at"])

    def mark_websocket_sent(self) -> None:
        """Mark WebSocket notification as sent."""
        self.websocket_sent = True
        self.websocket_sent_at = timezone.now()
        if self.status == self.Status.PENDING:
            self.status = self.Status.SENT
        self.save(update_fields=["websocket_sent", "websocket_sent_at", "status", "updated_at"])

    @property
    def is_read(self) -> bool:
        """Check if notification has been read."""
        return self.read_at is not None

    @property
    def is_archived(self) -> bool:
        """Check if notification has been archived."""
        return self.archived_at is not None


class NotificationPreference(TenantModel):
    """User preferences for notifications.

    Controls which notifications a user receives and through which channels.
    """

    class EmailFrequency(models.TextChoices):
        """Email frequency choices."""

        IMMEDIATE = "immediate", "Immediate"
        DAILY = "daily", "Daily Digest"
        WEEKLY = "weekly", "Weekly Digest"
        NEVER = "never", "Never"

    # User
    user_id = models.UUIDField(
        db_index=True,
        help_text="User these preferences belong to.",
    )

    # Category
    category = models.CharField(
        max_length=20,
        choices=Notification.Category.choices,
        help_text="Notification category.",
    )

    # Channel preferences
    in_app_enabled = models.BooleanField(
        default=True,
        help_text="Show in-app notifications.",
    )
    email_enabled = models.BooleanField(
        default=True,
        help_text="Send email notifications.",
    )
    push_enabled = models.BooleanField(
        default=False,
        help_text="Send push notifications (future).",
    )

    # Email settings
    email_frequency = models.CharField(
        max_length=20,
        choices=EmailFrequency.choices,
        default=EmailFrequency.IMMEDIATE,
    )

    # Disabled specific types (JSON array of notification type strings)
    disabled_types = models.JSONField(
        default=list,
        blank=True,
        help_text="List of disabled notification types.",
    )

    class Meta:
        db_table = "notification_preferences"
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
        unique_together = [["user_id", "category"]]
        indexes = [
            models.Index(
                fields=["user_id", "category"],
                name="idx_pref_user_category",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} - {self.category}"

    def is_type_enabled(self, notification_type: str) -> bool:
        """Check if a specific notification type is enabled."""
        return notification_type not in self.disabled_types

    @classmethod
    def get_or_create_defaults(cls, user_id, tenant_id) -> list["NotificationPreference"]:
        """Get or create default preferences for a user."""
        preferences = []

        for category in Notification.Category:
            pref, created = cls.objects.get_or_create(
                user_id=user_id,
                category=category.value,
                defaults={
                    "tenant_id": tenant_id,
                    "in_app_enabled": True,
                    "email_enabled": category.value in ["account", "social"],
                    "push_enabled": False,
                },
            )
            preferences.append(pref)

        return preferences
