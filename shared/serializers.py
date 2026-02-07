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
