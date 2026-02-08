"""DRF serializers for the accounts module."""

from __future__ import annotations

from typing import Any

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from modules.accounts.domain.services import default_password_policy
from modules.accounts.infrastructure.models import User
from modules.finance.domain.value_objects import Currency


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user details."""

    full_name = serializers.CharField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "tenant_id",
            "email",
            "first_name",
            "last_name",
            "default_currency",
            "full_name",
            "role",
            "status",
            "is_email_verified",
            "is_locked",
            "last_login_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tenant_id",
            "email",
            "role",
            "status",
            "is_email_verified",
            "last_login_at",
            "created_at",
            "updated_at",
        ]


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")

    def validate_email(self, value: str) -> str:
        """Validate email is not already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_("Email is already registered."))
        return value.lower()

    def validate_password(self, value: str) -> str:
        """Validate password meets policy requirements."""
        violations = default_password_policy.validate(value)
        if violations:
            raise serializers.ValidationError(violations)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate password confirmation matches."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        """Create new user."""
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            email=validated_data["email"],
            password=password,
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer with tenant and role claims."""

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate credentials and check account status."""
        email = attrs.get("email", "").lower()
        password = attrs.get("password", "")

        # Get user to check status before authentication
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"detail": _("Invalid email or password.")},
                code="invalid_credentials",
            )

        # Check if account is locked
        if user.is_locked:
            raise serializers.ValidationError(
                {"detail": _("Account is locked. Please try again later.")},
                code="account_locked",
            )

        # Check if account is active
        if user.status != User.Status.ACTIVE:
            if user.status == User.Status.PENDING:
                raise serializers.ValidationError(
                    {"detail": _("Please verify your email address.")},
                    code="email_not_verified",
                )
            raise serializers.ValidationError(
                {"detail": _("Account is not active.")},
                code="account_not_active",
            )

        # Authenticate
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if not user:
            # Record failed attempt
            try:
                failed_user = User.objects.get(email__iexact=email)
                failed_user.record_failed_login()
            except User.DoesNotExist:
                pass

            raise serializers.ValidationError(
                {"detail": _("Invalid email or password.")},
                code="invalid_credentials",
            )

        # Record successful login
        user.record_successful_login()

        # Get tokens
        data = super().validate(attrs)

        # Add user data to response
        data["user"] = UserSerializer(user).data

        return data

    @classmethod
    def get_token(cls, user: User) -> Any:
        """Generate token with custom claims."""
        token = super().get_token(user)

        # Add custom claims
        token["tenant_id"] = str(user.tenant_id)
        token["email"] = user.email
        token["role"] = user.role

        return token


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification."""

    token = serializers.CharField()


class RequestPasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request."""

    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for password reset."""

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)

    def validate_password(self, value: str) -> str:
        """Validate password meets policy requirements."""
        violations = default_password_policy.validate(value)
        if violations:
            raise serializers.ValidationError(violations)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate password confirmation matches."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": _("Passwords do not match.")}
            )
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_new_password(self, value: str) -> str:
        """Validate password meets policy requirements."""
        violations = default_password_policy.validate(value)
        if violations:
            raise serializers.ValidationError(violations)
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Validate passwords."""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": _("Passwords do not match.")}
            )

        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": _("Current password is incorrect.")}
            )

        return attrs


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "default_currency"]

    def validate_default_currency(self, value: str) -> str:
        """Validate currency code is supported."""
        if not Currency.is_supported(value):
            raise serializers.ValidationError(
                _("Unsupported currency: %(currency)s") % {"currency": value}
            )
        return value.upper()
