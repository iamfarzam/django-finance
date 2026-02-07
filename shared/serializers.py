"""Shared serializers for Django Finance.

This module provides:
- Custom JWT token serializer with tenant claims
- Base serializers for common patterns
"""

from __future__ import annotations

from typing import Any, ClassVar

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer that includes tenant claims.

    Extends the default token to include:
    - tenant_id: The user's tenant UUID
    - role: The user's role (user, premium, superadmin)
    """

    @classmethod
    def get_token(cls, user: Any) -> Any:
        """Generate token with custom claims.

        Args:
            user: The authenticated user.

        Returns:
            Token with custom claims added.
        """
        token = super().get_token(user)

        # Add tenant_id claim
        if hasattr(user, "tenant_id"):
            token["tenant_id"] = str(user.tenant_id)

        # Add role claim
        if hasattr(user, "role"):
            token["role"] = user.role
        elif user.is_staff:
            token["role"] = "superadmin"
        else:
            token["role"] = "user"

        # Add email claim
        token["email"] = user.email

        return token


class BaseSerializer(serializers.Serializer):
    """Base serializer with common functionality.

    Provides:
    - Standard error message formatting
    - Common field definitions
    """

    pass


class BaseModelSerializer(serializers.ModelSerializer):
    """Base model serializer with common functionality.

    Provides:
    - Read-only id, created_at, updated_at fields
    - Standard error message formatting
    """

    id = serializers.UUIDField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class TenantModelSerializer(BaseModelSerializer):
    """Base serializer for tenant-scoped models.

    Automatically excludes tenant_id from input and
    sets it from request context on create.
    """

    tenant_id = serializers.UUIDField(read_only=True)

    def create(self, validated_data: dict[str, Any]) -> Any:
        """Create instance with tenant_id from request context.

        Args:
            validated_data: Validated data from request.

        Returns:
            Created model instance.
        """
        from shared.middleware import get_tenant_id

        tenant_id = get_tenant_id()
        if tenant_id:
            validated_data["tenant_id"] = tenant_id

        return super().create(validated_data)


class FieldPermissionMixin:
    """Mixin for serializers that support field-level permissions.

    This mixin allows you to define which fields require premium access
    and optionally mask those fields for non-premium users instead of
    hiding them completely.

    Usage:
        class AccountSerializer(FieldPermissionMixin, ModelSerializer):
            # Fields only visible to premium users
            premium_fields = {
                "account_number_masked": "finance.view_sensitive",
                "interest_rate": "finance.view_rates",
                "notes": "finance.view_notes",
            }

            # Masking for non-premium (show field but masked value)
            masked_fields = {
                "account_number_masked": "****",
            }

            class Meta:
                model = Account
                fields = ["id", "name", "account_number_masked", "interest_rate", "notes"]

    Attributes:
        premium_fields: Dict mapping field name to required feature code.
        masked_fields: Dict mapping field name to masked value for non-premium users.
        hide_premium_fields: If True, hide fields entirely; if False, mask them.
    """

    # Field name -> feature code required
    premium_fields: ClassVar[dict[str, str]] = {}

    # Field name -> masked value for non-premium users
    masked_fields: ClassVar[dict[str, Any]] = {}

    # Whether to hide premium fields entirely or show masked values
    hide_premium_fields: ClassVar[bool] = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the serializer and filter fields based on permissions."""
        super().__init__(*args, **kwargs)
        self._filter_premium_fields()

    def _filter_premium_fields(self) -> None:
        """Filter out premium fields the user doesn't have access to."""
        if not self.premium_fields:
            return

        # Get user from context
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return

        user = request.user
        if not user or not user.is_authenticated:
            # For unauthenticated users, hide all premium fields
            if self.hide_premium_fields:
                for field_name in self.premium_fields:
                    self.fields.pop(field_name, None)
            return

        # Check each premium field
        from modules.subscriptions.domain.services import PermissionService

        for field_name, feature_code in self.premium_fields.items():
            if field_name not in self.fields:
                continue

            has_access = PermissionService.has_feature(user, feature_code)

            if not has_access:
                if self.hide_premium_fields:
                    # Completely remove the field
                    self.fields.pop(field_name, None)
                # If not hiding, the to_representation will handle masking

    def to_representation(self, instance: Any) -> dict[str, Any]:
        """Convert instance to representation, masking premium fields if needed.

        Args:
            instance: The model instance to serialize.

        Returns:
            Dictionary representation with masked values for non-premium fields.
        """
        data = super().to_representation(instance)  # type: ignore[misc]

        if self.hide_premium_fields or not self.masked_fields:
            return data

        # Get user from context
        request = self.context.get("request")
        if not request or not hasattr(request, "user"):
            return data

        user = request.user
        if not user or not user.is_authenticated:
            # Mask all premium fields for unauthenticated users
            for field_name, mask_value in self.masked_fields.items():
                if field_name in data:
                    data[field_name] = mask_value
            return data

        # Check and mask each premium field
        from modules.subscriptions.domain.services import PermissionService

        for field_name, feature_code in self.premium_fields.items():
            if field_name not in data:
                continue

            has_access = PermissionService.has_feature(user, feature_code)

            if not has_access and field_name in self.masked_fields:
                data[field_name] = self.masked_fields[field_name]

        return data


class ErrorDetailSerializer(serializers.Serializer):
    """Serializer for field-level error details."""

    field = serializers.CharField()
    code = serializers.CharField()
    message = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for standardized error responses.

    Used for OpenAPI documentation.
    """

    code = serializers.CharField(help_text="Machine-readable error code")
    message = serializers.CharField(help_text="Human-readable error message")
    details = ErrorDetailSerializer(
        many=True,
        required=False,
        help_text="Field-level error details",
    )
    correlation_id = serializers.CharField(
        required=False,
        help_text="Request correlation ID for support",
    )


class PaginatedResponseSerializer(serializers.Serializer):
    """Serializer for paginated responses.

    Used for OpenAPI documentation.
    """

    class MetaSerializer(serializers.Serializer):
        """Pagination metadata serializer."""

        class PaginationSerializer(serializers.Serializer):
            """Cursor pagination serializer."""

            cursor = serializers.CharField(
                allow_null=True,
                help_text="Cursor for the next page",
            )
            has_next = serializers.BooleanField(help_text="Whether there is a next page")
            has_previous = serializers.BooleanField(
                help_text="Whether there is a previous page"
            )

        pagination = PaginationSerializer()

    data = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of items",
    )
    meta = MetaSerializer()
