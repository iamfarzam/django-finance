"""Unit tests for subscription services."""

from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from modules.subscriptions.domain.enums import (
    FeatureCode,
    LimitKey,
    SubscriptionStatus,
    TierCode,
)
from modules.subscriptions.domain.services import (
    PermissionContext,
    PermissionService,
    UsageLimitService,
)


class TestPermissionContext:
    """Tests for PermissionContext dataclass."""

    def test_has_feature_when_feature_present(self):
        """Test has_feature returns True when feature is in the list."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            features=["reports.advanced", "export.pdf"],
        )

        assert context.has_feature("reports.advanced") is True
        assert context.has_feature("export.pdf") is True

    def test_has_feature_when_feature_missing(self):
        """Test has_feature returns False when feature is not in the list."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            features=["reports.advanced"],
        )

        assert context.has_feature("export.pdf") is False
        assert context.has_feature("api.access") is False

    def test_get_limit_returns_value_when_set(self):
        """Test get_limit returns the limit value when set."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            limits={"accounts_max": 3, "transactions_monthly": 500},
        )

        assert context.get_limit("accounts_max") == 3
        assert context.get_limit("transactions_monthly") == 500

    def test_get_limit_returns_none_when_not_set(self):
        """Test get_limit returns None when limit is not set."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            limits={"accounts_max": 3},
        )

        assert context.get_limit("transactions_monthly") is None

    def test_is_limit_unlimited_when_not_in_limits(self):
        """Test is_limit_unlimited returns True when limit is not set."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            limits={"accounts_max": 3},
        )

        assert context.is_limit_unlimited("transactions_monthly") is True

    def test_is_limit_unlimited_when_zero(self):
        """Test is_limit_unlimited returns True when limit is 0."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            limits={"accounts_max": 0},
        )

        assert context.is_limit_unlimited("accounts_max") is True

    def test_is_limit_unlimited_when_set_nonzero(self):
        """Test is_limit_unlimited returns False when limit is non-zero."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            limits={"accounts_max": 3},
        )

        assert context.is_limit_unlimited("accounts_max") is False

    def test_default_values(self):
        """Test that default values are set correctly."""
        context = PermissionContext(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
        )

        assert context.tier_code == TierCode.FREE.value
        assert context.status == SubscriptionStatus.ACTIVE.value
        assert context.features == []
        assert context.limits == {}
        assert context.is_premium is False
        assert context.expires_at is None


class TestPermissionService:
    """Tests for PermissionService."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        return user

    @pytest.fixture
    def mock_subscription(self):
        """Create a mock subscription object."""
        subscription = MagicMock()
        subscription.tier = MagicMock()
        subscription.tier.code = "premium"
        subscription.tier.features = ["reports.advanced", "export.pdf", "api.access"]
        subscription.tier.limits = {}
        subscription.status = "active"
        subscription.current_period_end = timezone.now() + timedelta(days=30)
        subscription.is_active.return_value = True
        return subscription

    def test_build_context_for_free_user(self, mock_user):
        """Test that free users get default free tier context."""
        with patch(
            "modules.subscriptions.infrastructure.models.Subscription.objects"
        ) as mock_qs:
            from modules.subscriptions.infrastructure.models import Subscription

            mock_qs.select_related.return_value.get.side_effect = (
                Subscription.DoesNotExist
            )

            context = PermissionService._build_context(mock_user)

            assert context.tier_code == TierCode.FREE.value
            assert context.is_premium is False
            assert LimitKey.ACCOUNTS_MAX.value in context.limits
            assert context.limits[LimitKey.ACCOUNTS_MAX.value] == 3
            assert FeatureCode.EXPORT_CSV.value in context.features

    def test_build_context_for_premium_user(self, mock_user, mock_subscription):
        """Test that premium users get premium tier context."""
        with patch(
            "modules.subscriptions.infrastructure.models.Subscription.objects"
        ) as mock_qs:
            mock_qs.select_related.return_value.get.return_value = mock_subscription

            context = PermissionService._build_context(mock_user)

            assert context.tier_code == "premium"
            assert context.is_premium is True
            assert "reports.advanced" in context.features
            assert "export.pdf" in context.features

    def test_has_feature_with_premium_feature(self, mock_user, mock_subscription):
        """Test has_feature returns True for premium features."""
        with patch(
            "modules.subscriptions.infrastructure.models.Subscription.objects"
        ) as mock_qs:
            mock_qs.select_related.return_value.get.return_value = mock_subscription

            # Clear cache to ensure fresh lookup
            PermissionService.invalidate_cache(mock_user.id)

            result = PermissionService.has_feature(mock_user, "reports.advanced")

            assert result is True

    def test_has_feature_without_premium_feature(self, mock_user):
        """Test has_feature returns False for missing features."""
        with patch(
            "modules.subscriptions.infrastructure.models.Subscription.objects"
        ) as mock_qs:
            from modules.subscriptions.infrastructure.models import Subscription

            mock_qs.select_related.return_value.get.side_effect = (
                Subscription.DoesNotExist
            )

            # Clear cache to ensure fresh lookup
            PermissionService.invalidate_cache(mock_user.id)

            result = PermissionService.has_feature(mock_user, "reports.advanced")

            assert result is False

    def test_check_limit_within_limit(self, mock_user):
        """Test check_limit returns True when within limit."""
        with patch(
            "modules.subscriptions.infrastructure.models.Subscription.objects"
        ) as mock_qs:
            from modules.subscriptions.infrastructure.models import Subscription

            mock_qs.select_related.return_value.get.side_effect = (
                Subscription.DoesNotExist
            )

            # Clear cache to ensure fresh lookup
            PermissionService.invalidate_cache(mock_user.id)

            result = PermissionService.check_limit(
                mock_user, LimitKey.ACCOUNTS_MAX.value, 2
            )

            assert result is True

    def test_check_limit_at_limit(self, mock_user):
        """Test check_limit returns False when at limit."""
        with patch(
            "modules.subscriptions.infrastructure.models.Subscription.objects"
        ) as mock_qs:
            from modules.subscriptions.infrastructure.models import Subscription

            mock_qs.select_related.return_value.get.side_effect = (
                Subscription.DoesNotExist
            )

            # Clear cache to ensure fresh lookup
            PermissionService.invalidate_cache(mock_user.id)

            result = PermissionService.check_limit(
                mock_user, LimitKey.ACCOUNTS_MAX.value, 3
            )

            assert result is False

    def test_check_limit_unlimited_for_premium(self, mock_user, mock_subscription):
        """Test check_limit returns True for premium users (unlimited)."""
        with patch(
            "modules.subscriptions.infrastructure.models.Subscription.objects"
        ) as mock_qs:
            mock_qs.select_related.return_value.get.return_value = mock_subscription

            # Clear cache to ensure fresh lookup
            PermissionService.invalidate_cache(mock_user.id)

            result = PermissionService.check_limit(
                mock_user, LimitKey.ACCOUNTS_MAX.value, 100
            )

            assert result is True

    def test_cache_invalidation(self, mock_user):
        """Test that cache invalidation works."""
        with patch.object(
            PermissionService, "_get_cache_key", return_value="test_key"
        ):
            with patch("modules.subscriptions.domain.services.cache") as mock_cache:
                PermissionService.invalidate_cache(mock_user.id)

                mock_cache.delete.assert_called_once_with("test_key")


class TestUsageLimitService:
    """Tests for UsageLimitService."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = uuid.uuid4()
        user.tenant_id = uuid.uuid4()
        return user

    def test_get_lifetime_count_accounts(self, mock_user):
        """Test getting account count."""
        with patch(
            "modules.finance.infrastructure.models.Account.objects"
        ) as mock_qs:
            mock_qs.filter.return_value.count.return_value = 2

            count = UsageLimitService._get_lifetime_count(mock_user, "accounts")

            assert count == 2
            mock_qs.filter.assert_called_once_with(tenant_id=mock_user.tenant_id)

    def test_get_lifetime_count_contacts(self, mock_user):
        """Test getting contact count."""
        with patch(
            "modules.social.infrastructure.models.Contact.objects"
        ) as mock_qs:
            mock_qs.filter.return_value.count.return_value = 5

            count = UsageLimitService._get_lifetime_count(mock_user, "contacts")

            assert count == 5

    def test_get_lifetime_count_expense_groups(self, mock_user):
        """Test getting expense group count."""
        with patch(
            "modules.social.infrastructure.models.ExpenseGroup.objects"
        ) as mock_qs:
            mock_qs.filter.return_value.count.return_value = 1

            count = UsageLimitService._get_lifetime_count(mock_user, "expense_groups")

            assert count == 1

    def test_get_lifetime_count_unknown_type(self, mock_user):
        """Test getting count for unknown type returns 0."""
        count = UsageLimitService._get_lifetime_count(mock_user, "unknown")

        assert count == 0

    def test_can_perform_action_allowed(self, mock_user):
        """Test can_perform_action returns True when allowed."""
        with (
            patch.object(
                PermissionService,
                "get_user_context",
            ) as mock_context,
            patch.object(
                UsageLimitService,
                "get_current_usage",
                return_value=2,
            ),
        ):
            context = PermissionContext(
                user_id=mock_user.id,
                tenant_id=mock_user.tenant_id,
                limits={LimitKey.ACCOUNTS_MAX.value: 3},
            )
            mock_context.return_value = context

            allowed, message = UsageLimitService.can_perform_action(
                mock_user, LimitKey.ACCOUNTS_MAX.value
            )

            assert allowed is True
            assert message is None

    def test_can_perform_action_denied(self, mock_user):
        """Test can_perform_action returns False when limit exceeded."""
        with (
            patch.object(
                PermissionService,
                "get_user_context",
            ) as mock_context,
            patch.object(
                UsageLimitService,
                "get_current_usage",
                return_value=3,
            ),
        ):
            context = PermissionContext(
                user_id=mock_user.id,
                tenant_id=mock_user.tenant_id,
                limits={LimitKey.ACCOUNTS_MAX.value: 3},
            )
            mock_context.return_value = context

            allowed, message = UsageLimitService.can_perform_action(
                mock_user, LimitKey.ACCOUNTS_MAX.value
            )

            assert allowed is False
            assert message is not None
            assert "limit exceeded" in message.lower()

    def test_can_perform_action_unlimited(self, mock_user):
        """Test can_perform_action returns True for unlimited tier."""
        with patch.object(
            PermissionService,
            "get_user_context",
        ) as mock_context:
            context = PermissionContext(
                user_id=mock_user.id,
                tenant_id=mock_user.tenant_id,
                limits={},  # Empty = unlimited
            )
            mock_context.return_value = context

            allowed, message = UsageLimitService.can_perform_action(
                mock_user, LimitKey.ACCOUNTS_MAX.value
            )

            assert allowed is True
            assert message is None
