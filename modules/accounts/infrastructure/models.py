"""Django ORM models for the accounts module.

These models implement persistence for the accounts domain.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from shared.models import BaseModel


class UserManager(BaseUserManager["User"]):
    """Custom user manager with email-based authentication."""

    def create_user(
        self,
        email: str,
        password: str | None = None,
        **extra_fields: Any,
    ) -> "User":
        """Create and save a regular user.

        Args:
            email: User's email address.
            password: User's password.
            **extra_fields: Additional fields for the user.

        Returns:
            Created user instance.
        """
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: str,
        **extra_fields: Any,
    ) -> "User":
        """Create and save a superuser.

        Args:
            email: User's email address.
            password: User's password.
            **extra_fields: Additional fields for the user.

        Returns:
            Created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.SUPERADMIN)
        extra_fields.setdefault("status", User.Status.ACTIVE)
        extra_fields.setdefault("is_email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email: str) -> "User":
        """Get user by natural key (email).

        Args:
            email: User's email address.

        Returns:
            User instance.
        """
        return self.get(email__iexact=email)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """Custom user model with email-based authentication and tenant support.

    This model extends Django's AbstractBaseUser to provide:
    - Email-based authentication (instead of username)
    - Tenant isolation for B2C multi-tenancy
    - Role-based access control
    - Account lockout protection
    - Soft delete support
    """

    class Role(models.TextChoices):
        """User role choices."""

        USER = "user", "User"
        PREMIUM = "premium", "Premium"
        SUPERADMIN = "superadmin", "Super Admin"

    class Status(models.TextChoices):
        """Account status choices."""

        PENDING = "pending", "Pending Verification"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        DELETED = "deleted", "Deleted"

    # Tenant
    tenant_id = models.UUIDField(
        db_index=True,
        help_text="Tenant this user belongs to. For B2C, typically equals user ID.",
    )

    # Authentication
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="User's email address (used for login).",
    )

    # Profile
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's first name.",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="User's last name.",
    )

    # Preferences
    default_currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Default currency for new records and views.",
    )

    # Role and status
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
        help_text="User's role in the system.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Account status.",
    )

    # Verification
    is_email_verified = models.BooleanField(
        default=False,
        help_text="Whether email has been verified.",
    )

    # Security
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts.",
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Account locked until this time.",
    )
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful login timestamp.",
    )

    # Soft delete
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether account has been soft deleted.",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When account was deleted.",
    )

    # Django auth fields
    is_staff = models.BooleanField(
        default=False,
        help_text="Whether user can access admin site.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether user account is active.",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "accounts_users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "email"], name="idx_user_tenant_email"),
            models.Index(fields=["tenant_id", "status"], name="idx_user_tenant_status"),
            models.Index(fields=["role", "status"], name="idx_user_role_status"),
        ]

    def __str__(self) -> str:
        return self.email

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save user, setting tenant_id if not set."""
        if not self.tenant_id:
            # For B2C, each user is their own tenant
            self.tenant_id = self.id or uuid.uuid4()
            if not self.id:
                self.id = self.tenant_id
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return timezone.now() < self.locked_until

    @property
    def can_login(self) -> bool:
        """Check if user can attempt login."""
        return (
            self.status == self.Status.ACTIVE
            and not self.is_locked
            and not self.is_deleted
        )

    def record_failed_login(self) -> None:
        """Record a failed login attempt."""
        from datetime import timedelta

        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save(update_fields=["failed_login_attempts", "locked_until", "updated_at"])

    def record_successful_login(self) -> None:
        """Record a successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = timezone.now()
        self.save(
            update_fields=[
                "failed_login_attempts",
                "locked_until",
                "last_login_at",
                "updated_at",
            ]
        )

    def verify_email(self) -> None:
        """Mark email as verified and activate account."""
        self.is_email_verified = True
        if self.status == self.Status.PENDING:
            self.status = self.Status.ACTIVE
        self.save(update_fields=["is_email_verified", "status", "updated_at"])


class EmailVerificationToken(BaseModel):
    """Token for email verification."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
    )
    email = models.EmailField(help_text="Email to verify.")
    token = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_email_verification_tokens"
        verbose_name = "Email Verification Token"
        verbose_name_plural = "Email Verification Tokens"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and self.used_at is None


class PasswordResetToken(BaseModel):
    """Token for password reset."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
    )
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounts_password_reset_tokens"
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        return not self.is_expired and self.used_at is None


class RefreshTokenBlacklist(BaseModel):
    """Blacklisted JWT refresh tokens."""

    token_jti = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="JWT ID of the blacklisted token.",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="blacklisted_tokens",
    )
    blacklisted_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="When the original token would have expired.",
    )

    class Meta:
        db_table = "accounts_refresh_token_blacklist"
        verbose_name = "Blacklisted Refresh Token"
        verbose_name_plural = "Blacklisted Refresh Tokens"

    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired tokens from blacklist.

        Returns:
            Number of tokens removed.
        """
        deleted, _ = cls.objects.filter(expires_at__lt=timezone.now()).delete()
        return deleted
