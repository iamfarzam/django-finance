"""Domain entities for the accounts module.

These are pure Python classes that represent core business concepts.
They contain business logic and validation rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    pass


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    """User role enumeration.

    Defines the available roles in the system with their permissions.
    """

    ANONYMOUS = "anonymous"
    USER = "user"
    PREMIUM = "premium"
    SUPERADMIN = "superadmin"

    @property
    def is_authenticated(self) -> bool:
        """Check if role represents an authenticated user."""
        return self != UserRole.ANONYMOUS

    @property
    def is_premium(self) -> bool:
        """Check if role has premium features."""
        return self in (UserRole.PREMIUM, UserRole.SUPERADMIN)

    @property
    def is_admin(self) -> bool:
        """Check if role has admin access."""
        return self == UserRole.SUPERADMIN


class UserStatus(str, Enum):
    """User account status."""

    PENDING = "pending"  # Email not verified
    ACTIVE = "active"  # Fully active
    SUSPENDED = "suspended"  # Temporarily suspended
    DELETED = "deleted"  # Soft deleted


@dataclass(frozen=True)
class Email:
    """Email value object with validation.

    Immutable value object that ensures email format validity.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate email format."""
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Check if email has valid format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def __str__(self) -> str:
        return self.value

    @property
    def domain(self) -> str:
        """Get email domain."""
        return self.value.split("@")[1]

    @property
    def local_part(self) -> str:
        """Get email local part (before @)."""
        return self.value.split("@")[0]


@dataclass
class User:
    """User domain entity.

    Represents a user account with all business logic.
    """

    id: UUID
    tenant_id: UUID
    email: Email
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING
    first_name: str = ""
    last_name: str = ""
    is_email_verified: bool = False
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Constants
    MAX_FAILED_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30

    @classmethod
    def create(
        cls,
        email: str,
        tenant_id: UUID | None = None,
        first_name: str = "",
        last_name: str = "",
    ) -> "User":
        """Factory method to create a new user.

        Args:
            email: User's email address.
            tenant_id: Optional tenant ID. Creates new tenant if None.
            first_name: User's first name.
            last_name: User's last name.

        Returns:
            New User instance in pending status.
        """
        user_id = uuid4()
        return cls(
            id=user_id,
            tenant_id=tenant_id or user_id,  # New user = new tenant for B2C
            email=Email(email),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.USER,
            status=UserStatus.PENDING,
        )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or str(self.email)

    @property
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return _utc_now() < self.locked_until

    @property
    def can_login(self) -> bool:
        """Check if user can attempt login."""
        return self.is_active and not self.is_locked

    def verify_email(self) -> None:
        """Mark email as verified and activate account."""
        self.is_email_verified = True
        if self.status == UserStatus.PENDING:
            self.status = UserStatus.ACTIVE
        self.updated_at = _utc_now()

    def record_failed_login(self) -> None:
        """Record a failed login attempt."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS:
            from datetime import timedelta

            self.locked_until = _utc_now() + timedelta(
                minutes=self.LOCKOUT_DURATION_MINUTES
            )
        self.updated_at = _utc_now()

    def record_successful_login(self) -> None:
        """Record a successful login."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = _utc_now()
        self.updated_at = _utc_now()

    def unlock(self) -> None:
        """Manually unlock the account."""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.updated_at = _utc_now()

    def suspend(self) -> None:
        """Suspend the user account."""
        self.status = UserStatus.SUSPENDED
        self.updated_at = _utc_now()

    def reactivate(self) -> None:
        """Reactivate a suspended account."""
        if self.status == UserStatus.SUSPENDED:
            self.status = UserStatus.ACTIVE
            self.updated_at = _utc_now()

    def soft_delete(self) -> None:
        """Soft delete the user account."""
        self.status = UserStatus.DELETED
        self.updated_at = _utc_now()

    def upgrade_to_premium(self) -> None:
        """Upgrade user to premium role."""
        if self.role == UserRole.USER:
            self.role = UserRole.PREMIUM
            self.updated_at = _utc_now()

    def downgrade_to_user(self) -> None:
        """Downgrade from premium to regular user."""
        if self.role == UserRole.PREMIUM:
            self.role = UserRole.USER
            self.updated_at = _utc_now()


@dataclass(frozen=True)
class EmailVerificationToken:
    """Email verification token value object."""

    token: str
    user_id: UUID
    email: Email
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return _utc_now() > self.expires_at


@dataclass(frozen=True)
class PasswordResetToken:
    """Password reset token value object."""

    token: str
    user_id: UUID
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        return _utc_now() > self.expires_at
