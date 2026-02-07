"""Data Transfer Objects for the accounts module.

DTOs are used to transfer data between layers without exposing
domain entities directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserDTO:
    """User data transfer object."""

    id: UUID
    tenant_id: UUID
    email: str
    role: str
    status: str
    first_name: str
    last_name: str
    full_name: str
    is_email_verified: bool
    is_active: bool
    is_locked: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class RegisterUserCommand:
    """Command to register a new user."""

    email: str
    password: str
    first_name: str = ""
    last_name: str = ""


@dataclass(frozen=True)
class LoginCommand:
    """Command to authenticate a user."""

    email: str
    password: str
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class VerifyEmailCommand:
    """Command to verify user email."""

    token: str


@dataclass(frozen=True)
class RequestPasswordResetCommand:
    """Command to request a password reset."""

    email: str


@dataclass(frozen=True)
class ResetPasswordCommand:
    """Command to reset password using token."""

    token: str
    new_password: str


@dataclass(frozen=True)
class ChangePasswordCommand:
    """Command to change password (authenticated user)."""

    user_id: UUID
    current_password: str
    new_password: str


@dataclass(frozen=True)
class UpdateProfileCommand:
    """Command to update user profile."""

    user_id: UUID
    first_name: str | None = None
    last_name: str | None = None


@dataclass(frozen=True)
class AuthTokensDTO:
    """Authentication tokens data transfer object."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900  # 15 minutes in seconds


@dataclass(frozen=True)
class LoginResultDTO:
    """Login result data transfer object."""

    user: UserDTO
    tokens: AuthTokensDTO
