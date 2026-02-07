"""Domain services for subscription management.

Provides PermissionService and UsageLimitService for checking
subscription features and usage limits.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from django.core.cache import cache
from django.utils import timezone

from modules.subscriptions.domain.enums import (
    FeatureCode,
    LimitKey,
    SubscriptionStatus,
    TierCode,
    UsageType,
)

if TYPE_CHECKING:
    from modules.accounts.infrastructure.models import User
    from modules.subscriptions.infrastructure.models import Subscription, SubscriptionTier


@dataclass
class PermissionContext:
    """Context object containing user's subscription permissions.

    Attributes:
        user_id: The user's ID.
        tenant_id: The user's tenant ID.
        tier_code: The subscription tier code.
        status: The subscription status.
        features: List of feature codes the user has access to.
        limits: Dictionary of usage limits.
        is_premium: Whether the user has premium features.
        expires_at: When the subscription expires.
    """

    user_id: uuid.UUID
    tenant_id: uuid.UUID
    tier_code: str = TierCode.FREE.value
    status: str = SubscriptionStatus.ACTIVE.value
    features: list[str] = field(default_factory=list)
    limits: dict[str, int] = field(default_factory=dict)
    is_premium: bool = False
    expires_at: datetime | None = None

    def has_feature(self, feature_code: str) -> bool:
        """Check if the context has a specific feature.

        Args:
            feature_code: The feature code to check.

        Returns:
            True if the user has access to the feature.
        """
        return feature_code in self.features

    def get_limit(self, limit_key: str) -> int | None:
        """Get a specific limit value.

        Args:
            limit_key: The limit key to look up.

        Returns:
            The limit value, or None if unlimited.
        """
        return self.limits.get(limit_key)

    def is_limit_unlimited(self, limit_key: str) -> bool:
        """Check if a limit is unlimited (not set or 0).

        Args:
            limit_key: The limit key to check.

        Returns:
            True if the limit is unlimited.
        """
        return limit_key not in self.limits or self.limits.get(limit_key) == 0


class PermissionService:
    """Service for checking subscription permissions.

    Provides cached access to user permission contexts and
    methods for checking features and limits.
    """

    CACHE_TTL = 300  # 5 minutes
    CACHE_PREFIX = "perm_ctx"

    @classmethod
    def _get_cache_key(cls, user_id: uuid.UUID) -> str:
        """Generate cache key for a user's permission context.

        Args:
            user_id: The user's ID.

        Returns:
            The cache key string.
        """
        return f"{cls.CACHE_PREFIX}:{user_id}"

    @classmethod
    def get_user_context(cls, user: User) -> PermissionContext:
        """Get the permission context for a user.

        Loads from cache if available, otherwise builds from database.

        Args:
            user: The user to get context for.

        Returns:
            The user's permission context.
        """
        cache_key = cls._get_cache_key(user.id)
        cached = cache.get(cache_key)

        if cached is not None:
            return cached

        context = cls._build_context(user)
        cache.set(cache_key, context, cls.CACHE_TTL)
        return context

    @classmethod
    def _build_context(cls, user: User) -> PermissionContext:
        """Build permission context from user's subscription.

        Args:
            user: The user to build context for.

        Returns:
            The built permission context.
        """
        from modules.subscriptions.infrastructure.models import Subscription

        # Default context for users without subscription
        context = PermissionContext(
            user_id=user.id,
            tenant_id=user.tenant_id,
            tier_code=TierCode.FREE.value,
            status=SubscriptionStatus.ACTIVE.value,
            features=[FeatureCode.EXPORT_CSV.value, FeatureCode.SOCIAL_BASIC.value],
            limits={
                LimitKey.ACCOUNTS_MAX.value: 3,
                LimitKey.TRANSACTIONS_MONTHLY.value: 500,
                LimitKey.CONTACTS_MAX.value: 10,
                LimitKey.EXPENSE_GROUPS_MAX.value: 2,
                LimitKey.API_CALLS_DAILY.value: 0,  # 0 = no API access
            },
            is_premium=False,
        )

        try:
            subscription = Subscription.objects.select_related("tier").get(user=user)

            if subscription.is_active():
                context.tier_code = subscription.tier.code
                context.status = subscription.status
                context.features = subscription.tier.features or []
                context.limits = subscription.tier.limits or {}
                context.is_premium = subscription.tier.code != TierCode.FREE.value
                context.expires_at = subscription.current_period_end

        except Subscription.DoesNotExist:
            pass

        return context

    @classmethod
    def has_feature(cls, user: User, feature_code: str) -> bool:
        """Check if a user has access to a specific feature.

        Args:
            user: The user to check.
            feature_code: The feature code to check.

        Returns:
            True if the user has access to the feature.
        """
        context = cls.get_user_context(user)
        return context.has_feature(feature_code)

    @classmethod
    def check_limit(cls, user: User, limit_key: str, current_count: int) -> bool:
        """Check if a user is within their usage limit.

        Args:
            user: The user to check.
            limit_key: The limit key to check.
            current_count: The current usage count.

        Returns:
            True if the user is within the limit.
        """
        context = cls.get_user_context(user)

        # Unlimited if not in limits
        if context.is_limit_unlimited(limit_key):
            return True

        limit = context.get_limit(limit_key)
        return current_count < limit

    @classmethod
    def invalidate_cache(cls, user_id: uuid.UUID) -> None:
        """Invalidate the cached permission context for a user.

        Call this when a user's subscription changes.

        Args:
            user_id: The user's ID.
        """
        cache_key = cls._get_cache_key(user_id)
        cache.delete(cache_key)


class UsageLimitService:
    """Service for tracking and enforcing usage limits."""

    @classmethod
    def get_current_usage(cls, user: User, usage_type: str) -> int:
        """Get the current usage count for a user.

        Args:
            user: The user to get usage for.
            usage_type: The type of usage to check.

        Returns:
            The current usage count.
        """
        from modules.subscriptions.infrastructure.models import UsageRecord

        today = timezone.now().date()

        if usage_type == UsageType.TRANSACTIONS_MONTHLY.value:
            # Monthly usage - get current month
            period_start = today.replace(day=1)
        elif usage_type == UsageType.API_CALLS_DAILY.value:
            # Daily usage
            period_start = today
        else:
            # Lifetime count - use model counts directly
            return cls._get_lifetime_count(user, usage_type)

        try:
            record = UsageRecord.objects.get(
                user=user,
                usage_type=usage_type,
                period_start=period_start,
            )
            return record.count
        except UsageRecord.DoesNotExist:
            return 0

    @classmethod
    def _get_lifetime_count(cls, user: User, usage_type: str) -> int:
        """Get lifetime count for non-periodic usage types.

        Args:
            user: The user to get count for.
            usage_type: The type of usage.

        Returns:
            The current count.
        """
        if usage_type == UsageType.ACCOUNTS.value:
            from modules.finance.infrastructure.models import Account

            return Account.objects.filter(tenant_id=user.tenant_id).count()

        if usage_type == UsageType.CONTACTS.value:
            from modules.social.infrastructure.models import Contact

            return Contact.objects.filter(tenant_id=user.tenant_id).count()

        if usage_type == UsageType.EXPENSE_GROUPS.value:
            from modules.social.infrastructure.models import ExpenseGroup

            return ExpenseGroup.objects.filter(tenant_id=user.tenant_id).count()

        return 0

    @classmethod
    def increment_usage(cls, user: User, usage_type: str, count: int = 1) -> int:
        """Increment the usage count for a user.

        Args:
            user: The user to increment usage for.
            usage_type: The type of usage.
            count: The amount to increment by.

        Returns:
            The new usage count.
        """
        from modules.subscriptions.infrastructure.models import UsageRecord

        today = timezone.now().date()

        if usage_type == UsageType.TRANSACTIONS_MONTHLY.value:
            period_start = today.replace(day=1)
            # Calculate period end (last day of month)
            if today.month == 12:
                period_end = today.replace(year=today.year + 1, month=1, day=1)
            else:
                period_end = today.replace(month=today.month + 1, day=1)
        elif usage_type == UsageType.API_CALLS_DAILY.value:
            period_start = today
            period_end = today
        else:
            # For lifetime counts, we don't track in UsageRecord
            return cls._get_lifetime_count(user, usage_type)

        record, created = UsageRecord.objects.get_or_create(
            user=user,
            usage_type=usage_type,
            period_start=period_start,
            defaults={
                "count": count,
                "period_end": period_end,
            },
        )

        if not created:
            record.count += count
            record.save(update_fields=["count", "updated_at"])

        return record.count

    @classmethod
    def can_perform_action(cls, user: User, limit_key: str) -> tuple[bool, str | None]:
        """Check if a user can perform an action based on their limits.

        Args:
            user: The user to check.
            limit_key: The limit key to check.

        Returns:
            Tuple of (allowed, error_message).
        """
        context = PermissionService.get_user_context(user)

        # Unlimited
        if context.is_limit_unlimited(limit_key):
            return True, None

        # Map limit keys to usage types
        usage_type_map = {
            LimitKey.ACCOUNTS_MAX.value: UsageType.ACCOUNTS.value,
            LimitKey.TRANSACTIONS_MONTHLY.value: UsageType.TRANSACTIONS_MONTHLY.value,
            LimitKey.CONTACTS_MAX.value: UsageType.CONTACTS.value,
            LimitKey.EXPENSE_GROUPS_MAX.value: UsageType.EXPENSE_GROUPS.value,
            LimitKey.API_CALLS_DAILY.value: UsageType.API_CALLS_DAILY.value,
        }

        usage_type = usage_type_map.get(limit_key)
        if not usage_type:
            return True, None

        current_count = cls.get_current_usage(user, usage_type)
        limit = context.get_limit(limit_key)

        if current_count >= limit:
            return False, f"Usage limit exceeded. Current: {current_count}, Limit: {limit}"

        return True, None
