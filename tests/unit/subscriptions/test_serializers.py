"""Unit tests for FieldPermissionMixin."""

from __future__ import annotations

import uuid
from typing import Any, ClassVar
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import serializers

from shared.serializers import FieldPermissionMixin


class SampleSerializer(FieldPermissionMixin, serializers.Serializer):
    """Sample serializer for testing FieldPermissionMixin."""

    # Premium field permissions
    premium_fields: ClassVar[dict[str, str]] = {
        "secret_field": "feature.premium",
        "notes": "feature.notes",
    }

    # Masking for non-premium users
    masked_fields: ClassVar[dict[str, Any]] = {
        "secret_field": "****",
    }

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    secret_field = serializers.CharField(max_length=100, required=False)
    notes = serializers.CharField(required=False)


class HiddenFieldSerializer(FieldPermissionMixin, serializers.Serializer):
    """Serializer that hides premium fields instead of masking."""

    # Premium field permissions
    premium_fields: ClassVar[dict[str, str]] = {
        "secret_field": "feature.premium",
    }

    # Hide premium fields instead of masking
    hide_premium_fields: ClassVar[bool] = True

    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=100)
    secret_field = serializers.CharField(max_length=100, required=False)


class TestFieldPermissionMixin:
    """Tests for FieldPermissionMixin."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = MagicMock()
        user.is_authenticated = True
        user.id = uuid.uuid4()
        return user

    @pytest.fixture
    def mock_request(self, mock_user):
        """Create a mock request with user."""
        request = MagicMock()
        request.user = mock_user
        return request

    def test_premium_user_sees_all_fields(self, mock_request):
        """Test that premium users see all fields unmasked."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=True,
        ):
            data = {
                "id": uuid.uuid4(),
                "name": "Test Item",
                "secret_field": "secret123",
                "notes": "Some notes",
            }

            serializer = SampleSerializer(data, context={"request": mock_request})
            result = serializer.data

            assert result["name"] == "Test Item"
            assert result["secret_field"] == "secret123"
            assert result["notes"] == "Some notes"

    def test_free_user_sees_masked_fields(self, mock_request):
        """Test that free users see masked premium fields."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=False,
        ):
            data = {
                "id": uuid.uuid4(),
                "name": "Test Item",
                "secret_field": "secret123",
                "notes": "Some notes",
            }

            serializer = SampleSerializer(data, context={"request": mock_request})
            result = serializer.data

            assert result["name"] == "Test Item"
            assert result["secret_field"] == "****"  # Masked
            # notes doesn't have a mask so it shows as-is
            assert result["notes"] == "Some notes"

    def test_hidden_fields_not_visible_to_free_user(self, mock_request):
        """Test that premium fields are hidden when hide_premium_fields is True."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=False,
        ):
            data = {
                "id": uuid.uuid4(),
                "name": "Test Item",
                "secret_field": "secret123",
            }

            serializer = HiddenFieldSerializer(
                data, context={"request": mock_request}
            )
            result = serializer.data

            assert result["name"] == "Test Item"
            assert "secret_field" not in result

    def test_hidden_fields_visible_to_premium_user(self, mock_request):
        """Test that premium fields are visible when user has feature."""
        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            return_value=True,
        ):
            data = {
                "id": uuid.uuid4(),
                "name": "Test Item",
                "secret_field": "secret123",
            }

            serializer = HiddenFieldSerializer(
                data, context={"request": mock_request}
            )
            result = serializer.data

            assert result["name"] == "Test Item"
            assert result["secret_field"] == "secret123"

    def test_unauthenticated_user_sees_masked_fields(self):
        """Test that unauthenticated users see masked fields."""
        request = MagicMock()
        request.user = MagicMock()
        request.user.is_authenticated = False

        data = {
            "id": uuid.uuid4(),
            "name": "Test Item",
            "secret_field": "secret123",
            "notes": "Some notes",
        }

        serializer = SampleSerializer(data, context={"request": request})
        result = serializer.data

        assert result["name"] == "Test Item"
        assert result["secret_field"] == "****"  # Masked

    def test_no_request_context_returns_normal_data(self):
        """Test that serializer works without request context."""
        data = {
            "id": uuid.uuid4(),
            "name": "Test Item",
            "secret_field": "secret123",
        }

        # No context or no request in context
        serializer = SampleSerializer(data, context={})
        result = serializer.data

        # Should return data as-is since we can't check permissions
        assert result["name"] == "Test Item"

    def test_partial_feature_access(self, mock_request):
        """Test that users can have access to some but not all features."""

        def has_feature_side_effect(user, feature_code):
            # User has notes feature but not premium feature
            return feature_code == "feature.notes"

        with patch(
            "modules.subscriptions.domain.services.PermissionService.has_feature",
            side_effect=has_feature_side_effect,
        ):
            data = {
                "id": uuid.uuid4(),
                "name": "Test Item",
                "secret_field": "secret123",
                "notes": "Some notes",
            }

            serializer = SampleSerializer(data, context={"request": mock_request})
            result = serializer.data

            assert result["name"] == "Test Item"
            assert result["secret_field"] == "****"  # No premium feature
            assert result["notes"] == "Some notes"  # Has notes feature
