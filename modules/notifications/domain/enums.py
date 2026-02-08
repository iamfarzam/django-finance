"""Enums for the notifications domain."""

from __future__ import annotations

from enum import Enum


class NotificationCategory(str, Enum):
    """Categories of notifications for grouping and preferences."""

    ACCOUNT = "account"  # Account-related (verification, password, security)
    FINANCE = "finance"  # Financial transactions, balances, reports
    SOCIAL = "social"  # Debts, settlements, expense groups
    SYSTEM = "system"  # System announcements, maintenance


class NotificationType(str, Enum):
    """Specific notification types within each category."""

    # Account notifications
    ACCOUNT_WELCOME = "account.welcome"
    ACCOUNT_EMAIL_VERIFIED = "account.email_verified"
    ACCOUNT_PASSWORD_CHANGED = "account.password_changed"
    ACCOUNT_PASSWORD_RESET = "account.password_reset"
    ACCOUNT_LOGIN_NEW_DEVICE = "account.login_new_device"
    ACCOUNT_SUBSCRIPTION_CHANGED = "account.subscription_changed"

    # Finance notifications
    FINANCE_TRANSACTION_CREATED = "finance.transaction_created"
    FINANCE_TRANSACTION_POSTED = "finance.transaction_posted"
    FINANCE_LARGE_TRANSACTION = "finance.large_transaction"
    FINANCE_LOW_BALANCE = "finance.low_balance"
    FINANCE_TRANSFER_COMPLETED = "finance.transfer_completed"
    FINANCE_ACCOUNT_CREATED = "finance.account_created"
    FINANCE_ACCOUNT_CLOSED = "finance.account_closed"
    FINANCE_NET_WORTH_MILESTONE = "finance.net_worth_milestone"

    # Social notifications
    SOCIAL_DEBT_CREATED = "social.debt_created"
    SOCIAL_DEBT_REMINDER = "social.debt_reminder"
    SOCIAL_DEBT_SETTLED = "social.debt_settled"
    SOCIAL_SETTLEMENT_RECEIVED = "social.settlement_received"
    SOCIAL_EXPENSE_ADDED = "social.expense_added"
    SOCIAL_GROUP_INVITATION = "social.group_invitation"
    SOCIAL_GROUP_EXPENSE_SPLIT = "social.group_expense_split"
    SOCIAL_BALANCE_UPDATED = "social.balance_updated"

    # System notifications
    SYSTEM_ANNOUNCEMENT = "system.announcement"
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_FEATURE_UPDATE = "system.feature_update"

    @property
    def category(self) -> NotificationCategory:
        """Get the category for this notification type."""
        prefix = self.value.split(".")[0]
        return NotificationCategory(prefix)


class NotificationChannel(str, Enum):
    """Delivery channels for notifications."""

    IN_APP = "in_app"  # Database-stored, shown in UI
    EMAIL = "email"  # Email delivery
    PUSH = "push"  # Push notifications (future)
    WEBSOCKET = "websocket"  # Real-time WebSocket


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"  # Informational, can be batched
    NORMAL = "normal"  # Standard delivery
    HIGH = "high"  # Immediate delivery
    URGENT = "urgent"  # Critical, all channels


class NotificationStatus(str, Enum):
    """Status of a notification."""

    PENDING = "pending"  # Created, not yet delivered
    SENT = "sent"  # Delivered to channel
    READ = "read"  # User has seen it
    ARCHIVED = "archived"  # User archived it
    FAILED = "failed"  # Delivery failed
