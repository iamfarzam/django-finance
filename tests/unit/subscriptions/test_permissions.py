"""Unit tests for subscription-based permission classes."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from shared.permissions import (
    CanExport,
    HasApiAccess,
    HasFeature,
    WithinUsageLimit,
)


class TestHasFeature:
    """Tests for HasFeature permission class."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with user."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.id = uuid.uuid4()
        return request

    @pytest.fixture
    def mock_view(self):
        """Create a mock view."""
        return MagicMock()

    def test_allows_access_with_feature(self, mock_request, mock_view):
        """Test that access is allowed when user has the feature."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=True,
        ):
            permission = HasFeature("reports.advanced")
            result = permission.has_permission(mock_request, mock_view)

            assert result is True

    def test_denies_access_without_feature(self, mock_request, mock_view):
        """Test that access is denied when user lacks the feature."""
        with (
            patch("shared.middleware.get_subscription_context", return_value=None),
            patch(
                "modules.subscriptions.domain.services.PermissionService.has_feature",
                return_value=False,
            ),
        ):
            permission = HasFeature("reports.advanced")
            result = permission.has_permission(mock_request, mock_view)

            assert result is False

    def test_allows_access_when_no_feature_specified(self, mock_request, mock_view):
        """Test that access is allowed when no feature is specified."""
        mock_view.feature_code = None

        permission = HasFeature()
        result = permission.has_permission(mock_request, mock_view)

        assert result is True

    def test_gets_feature_from_view(self, mock_request, mock_view):
        """Test that feature code is read from view if not specified."""
        mock_view.feature_code = "reports.advanced"

        with (
            patch("shared.middleware.get_subscription_context", return_value=None),
            patch(
                "modules.subscriptions.domain.services.PermissionService.has_feature",
                return_value=True,
            ) as mock_has_feature,
        ):
            permission = HasFeature()
            permission.has_permission(mock_request, mock_view)

            mock_has_feature.assert_called_once_with(
                mock_request.user, "reports.advanced"
            )

    def test_denies_unauthenticated_users(self, mock_view):
        """Test that unauthenticated users are denied."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False

        permission = HasFeature("reports.advanced")
        result = permission.has_permission(request, mock_view)

        assert result is False


class TestWithinUsageLimit:
    """Tests for WithinUsageLimit permission class."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with user."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.id = uuid.uuid4()
        return request

    @pytest.fixture
    def mock_view(self):
        """Create a mock view with create action."""
        view = MagicMock()
        view.action = "create"
        return view

    def test_allows_access_within_limit(self, mock_request, mock_view):
        """Test that access is allowed when within usage limit."""
        with patch(
            "modules.subscriptions.domain.services.UsageLimitService.can_perform_action",
            return_value=(True, None),
        ):
            permission = WithinUsageLimit("accounts_max")
            result = permission.has_permission(mock_request, mock_view)

            assert result is True

    def test_denies_access_over_limit(self, mock_request, mock_view):
        """Test that access is denied when over usage limit."""
        with patch(
            "modules.subscriptions.domain.services.UsageLimitService.can_perform_action",
            return_value=(False, "Usage limit exceeded. Current: 3, Limit: 3"),
        ):
            permission = WithinUsageLimit("accounts_max")
            result = permission.has_permission(mock_request, mock_view)

            assert result is False
            assert "limit exceeded" in permission.message.lower()

    def test_allows_non_create_actions(self, mock_request):
        """Test that non-create actions are allowed."""
        view = MagicMock()
        view.action = "list"

        permission = WithinUsageLimit("accounts_max")
        result = permission.has_permission(mock_request, view)

        assert result is True

    def test_allows_when_no_limit_specified(self, mock_request, mock_view):
        """Test that access is allowed when no limit is specified."""
        mock_view.limit_key = None

        permission = WithinUsageLimit()
        result = permission.has_permission(mock_request, mock_view)

        assert result is True

    def test_denies_unauthenticated_users(self, mock_view):
        """Test that unauthenticated users are denied."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False

        permission = WithinUsageLimit("accounts_max")
        result = permission.has_permission(request, mock_view)

        assert result is False


class TestHasApiAccess:
    """Tests for HasApiAccess permission class."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with user."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.id = uuid.uuid4()
        return request

    @pytest.fixture
    def mock_view(self):
        """Create a mock view."""
        return MagicMock()

    def test_allows_session_requests(self, mock_request, mock_view):
        """Test that session-based requests are always allowed."""
        mock_request.auth = None  # No JWT token = session request

        permission = HasApiAccess()
        result = permission.has_permission(mock_request, mock_view)

        assert result is True

    def test_allows_api_requests_with_api_access(self, mock_request, mock_view):
        """Test that API requests are allowed for users with api.access feature."""
        mock_request.auth = MagicMock()  # Has JWT token

        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=True,
        ):
            permission = HasApiAccess()
            result = permission.has_permission(mock_request, mock_view)

            assert result is True

    def test_denies_api_requests_without_api_access(self, mock_request, mock_view):
        """Test that API requests are denied for users without api.access."""
        mock_request.auth = MagicMock()  # Has JWT token

        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=False,
        ):
            permission = HasApiAccess()
            result = permission.has_permission(mock_request, mock_view)

            assert result is False

    def test_denies_unauthenticated_users(self, mock_view):
        """Test that unauthenticated users are denied."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False

        permission = HasApiAccess()
        result = permission.has_permission(request, mock_view)

        assert result is False


class TestCanExport:
    """Tests for CanExport permission class."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request with user."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.id = uuid.uuid4()
        return request

    @pytest.fixture
    def mock_view(self):
        """Create a mock view."""
        return MagicMock()

    def test_allows_csv_export_for_all(self, mock_request, mock_view):
        """Test that CSV export is allowed for all authenticated users."""
        permission = CanExport("csv")
        result = permission.has_permission(mock_request, mock_view)

        assert result is True

    def test_allows_json_export_for_premium(self, mock_request, mock_view):
        """Test that JSON export is allowed for premium users."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=True,
        ):
            permission = CanExport("json")
            result = permission.has_permission(mock_request, mock_view)

            assert result is True

    def test_denies_json_export_for_free(self, mock_request, mock_view):
        """Test that JSON export is denied for free users."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=False,
        ):
            permission = CanExport("json")
            result = permission.has_permission(mock_request, mock_view)

            assert result is False

    def test_allows_pdf_export_for_premium(self, mock_request, mock_view):
        """Test that PDF export is allowed for premium users."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=True,
        ):
            permission = CanExport("pdf")
            result = permission.has_permission(mock_request, mock_view)

            assert result is True

    def test_denies_pdf_export_for_free(self, mock_request, mock_view):
        """Test that PDF export is denied for free users."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=False,
        ):
            permission = CanExport("pdf")
            result = permission.has_permission(mock_request, mock_view)

            assert result is False

    def test_denies_unknown_format(self, mock_request, mock_view):
        """Test that unknown export formats are denied."""
        permission = CanExport("xlsx")
        result = permission.has_permission(mock_request, mock_view)

        assert result is False

    def test_denies_unauthenticated_users(self, mock_view):
        """Test that unauthenticated users are denied."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False

        permission = CanExport("csv")
        result = permission.has_permission(request, mock_view)

        assert result is False
