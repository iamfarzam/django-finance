"""Domain events for the accounts module.

These events are published when significant domain actions occur.
They follow the event naming convention: accounts.<entity>.<action>
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import UUID

from pydantic import Field

from contracts.events.base import BaseEvent


class UserCreated(BaseEvent):
    """Event published when a new user account is created."""

    _event_type: ClassVar[str] = "accounts.user.created"

    user_id: UUID
    email: str
    role: str


class UserEmailVerified(BaseEvent):
    """Event published when a user verifies their email."""

    _event_type: ClassVar[str] = "accounts.user.email_verified"

    user_id: UUID
    email: str


class UserLoggedIn(BaseEvent):
    """Event published when a user successfully logs in."""

    _event_type: ClassVar[str] = "accounts.user.logged_in"

    user_id: UUID
    ip_address: str | None = None
    user_agent: str | None = None


class UserLoggedOut(BaseEvent):
    """Event published when a user logs out."""

    _event_type: ClassVar[str] = "accounts.user.logged_out"

    user_id: UUID


class UserLoginFailed(BaseEvent):
    """Event published when a login attempt fails."""

    _event_type: ClassVar[str] = "accounts.user.login_failed"

    email: str
    ip_address: str | None = None
    reason: str = "invalid_credentials"


class UserAccountLocked(BaseEvent):
    """Event published when a user account is locked."""

    _event_type: ClassVar[str] = "accounts.user.account_locked"

    user_id: UUID
    locked_until: datetime
    reason: str = "too_many_failed_attempts"


class UserAccountUnlocked(BaseEvent):
    """Event published when a user account is unlocked."""

    _event_type: ClassVar[str] = "accounts.user.account_unlocked"

    user_id: UUID
    unlocked_by: UUID | None = None  # None if automatic


class UserPasswordChanged(BaseEvent):
    """Event published when a user changes their password."""

    _event_type: ClassVar[str] = "accounts.user.password_changed"

    user_id: UUID
    changed_via: str = "user_action"  # user_action, reset_token, admin


class UserPasswordResetRequested(BaseEvent):
    """Event published when a password reset is requested."""

    _event_type: ClassVar[str] = "accounts.user.password_reset_requested"

    user_id: UUID
    email: str


class UserProfileUpdated(BaseEvent):
    """Event published when a user updates their profile."""

    _event_type: ClassVar[str] = "accounts.user.profile_updated"

    user_id: UUID
    updated_fields: list[str] = Field(default_factory=list)


class UserRoleChanged(BaseEvent):
    """Event published when a user's role changes."""

    _event_type: ClassVar[str] = "accounts.user.role_changed"

    user_id: UUID
    old_role: str
    new_role: str
    changed_by: UUID | None = None


class UserDeleted(BaseEvent):
    """Event published when a user account is deleted."""

    _event_type: ClassVar[str] = "accounts.user.deleted"

    user_id: UUID
    deletion_type: str = "soft"  # soft or hard
