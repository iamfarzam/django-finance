"""Enums for the subscriptions module.

Defines tier codes, subscription statuses, and usage types.
"""

from __future__ import annotations

from enum import Enum


class TierCode(str, Enum):
    """Subscription tier codes."""

    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status values."""

    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    INCOMPLETE = "incomplete"


class UsageType(str, Enum):
    """Types of usage that can be tracked."""

    ACCOUNTS = "accounts"
    TRANSACTIONS_MONTHLY = "transactions_monthly"
    CONTACTS = "contacts"
    EXPENSE_GROUPS = "expense_groups"
    API_CALLS_DAILY = "api_calls_daily"


class FeatureCode(str, Enum):
    """Feature codes for subscription tiers."""

    # Reports
    REPORTS_ADVANCED = "reports.advanced"
    REPORTS_EXPORT_PDF = "reports.export_pdf"

    # Export
    EXPORT_CSV = "export.csv"
    EXPORT_JSON = "export.json"
    EXPORT_PDF = "export.pdf"

    # API
    API_ACCESS = "api.access"

    # Social
    SOCIAL_BASIC = "social.basic"
    SOCIAL_FULL = "social.full"

    # Finance
    FINANCE_VIEW_SENSITIVE = "finance.view_sensitive"
    FINANCE_VIEW_RATES = "finance.view_rates"
    FINANCE_VIEW_NOTES = "finance.view_notes"
    FINANCE_BULK_IMPORT = "finance.bulk_import"
    FINANCE_ANALYTICS = "finance.analytics"

    # Expense Groups
    EXPENSE_GROUPS_UNLIMITED_MEMBERS = "expense_groups.unlimited_members"


class LimitKey(str, Enum):
    """Keys for usage limits in tier definitions."""

    ACCOUNTS_MAX = "accounts_max"
    TRANSACTIONS_MONTHLY = "transactions_monthly"
    CONTACTS_MAX = "contacts_max"
    EXPENSE_GROUPS_MAX = "expense_groups_max"
    API_CALLS_DAILY = "api_calls_daily"
