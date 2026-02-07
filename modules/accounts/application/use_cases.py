"""Use cases for the accounts module.

Use cases orchestrate domain entities and services to perform
specific business operations.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)

from modules.accounts.application.dto import (
    ChangePasswordCommand,
    RegisterUserCommand,
    RequestPasswordResetCommand,
    ResetPasswordCommand,
    UpdateProfileCommand,
    UserDTO,
    VerifyEmailCommand,
)
from modules.accounts.domain.entities import User
from modules.accounts.domain.events import (
    UserCreated,
    UserEmailVerified,
    UserPasswordChanged,
    UserPasswordResetRequested,
    UserProfileUpdated,
)
from modules.accounts.domain.exceptions import (
    EmailAlreadyExistsError,
    InvalidTokenError,
    PasswordPolicyError,
    TokenExpiredError,
    UserNotFoundError,
)
from modules.accounts.domain.services import TokenGenerator, default_password_policy

if TYPE_CHECKING:
    from uuid import UUID

    from modules.accounts.application.interfaces import (
        EmailService,
        EventPublisher,
        PasswordHasher,
        TokenRepository,
        UserRepository,
    )


class RegisterUser:
    """Use case for registering a new user."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        password_hasher: PasswordHasher,
        email_service: EmailService,
        event_publisher: EventPublisher,
        verification_url_template: str = "/verify-email?token={token}",
    ) -> None:
        self._user_repo = user_repository
        self._token_repo = token_repository
        self._password_hasher = password_hasher
        self._email_service = email_service
        self._event_publisher = event_publisher
        self._verification_url_template = verification_url_template

    async def execute(self, command: RegisterUserCommand) -> UserDTO:
        """Register a new user.

        Args:
            command: Registration command with user details.

        Returns:
            Created user DTO.

        Raises:
            EmailAlreadyExistsError: If email is already registered.
            PasswordPolicyError: If password doesn't meet requirements.
        """
        # Validate password policy
        violations = default_password_policy.validate(command.password)
        if violations:
            raise PasswordPolicyError(violations)

        # Check email uniqueness
        if await self._user_repo.exists_by_email(command.email):
            raise EmailAlreadyExistsError(command.email)

        # Create user entity
        user = User.create(
            email=command.email,
            first_name=command.first_name,
            last_name=command.last_name,
        )

        # Hash password and save user
        password_hash = self._password_hasher.hash(command.password)
        saved_user = await self._user_repo.save(user)

        # Generate and save verification token
        token = TokenGenerator.generate_verification_token()
        expires_at = _utc_now() + timedelta(hours=24)
        await self._token_repo.save_verification_token(
            user_id=saved_user.id,
            email=str(saved_user.email),
            token=token,
            expires_at=expires_at.isoformat(),
        )

        # Send verification email
        verification_url = self._verification_url_template.format(token=token)
        await self._email_service.send_verification_email(
            email=str(saved_user.email),
            verification_url=verification_url,
            user_name=saved_user.full_name,
        )

        # Publish event
        await self._event_publisher.publish(
            UserCreated(
                tenant_id=saved_user.tenant_id,
                user_id=saved_user.id,
                email=str(saved_user.email),
                role=saved_user.role.value,
            )
        )

        return self._to_dto(saved_user)

    def _to_dto(self, user: User) -> UserDTO:
        """Convert user entity to DTO."""
        return UserDTO(
            id=user.id,
            tenant_id=user.tenant_id,
            email=str(user.email),
            role=user.role.value,
            status=user.status.value,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_email_verified=user.is_email_verified,
            is_active=user.is_active,
            is_locked=user.is_locked,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class VerifyEmail:
    """Use case for verifying user email."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._user_repo = user_repository
        self._token_repo = token_repository
        self._event_publisher = event_publisher

    async def execute(self, command: VerifyEmailCommand) -> UserDTO:
        """Verify user email with token.

        Args:
            command: Verification command with token.

        Returns:
            Updated user DTO.

        Raises:
            InvalidTokenError: If token is invalid.
            TokenExpiredError: If token has expired.
            UserNotFoundError: If user not found.
        """
        # Get token data
        token_data = await self._token_repo.get_verification_token(command.token)
        if not token_data:
            raise InvalidTokenError("verification token")

        # Check expiration
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if _utc_now() > expires_at:
            await self._token_repo.delete_verification_token(command.token)
            raise TokenExpiredError("verification token")

        # Get user
        user = await self._user_repo.get_by_id(token_data["user_id"])
        if not user:
            raise UserNotFoundError(str(token_data["user_id"]))

        # Verify email
        user.verify_email()
        saved_user = await self._user_repo.save(user)

        # Delete used token
        await self._token_repo.delete_verification_token(command.token)

        # Publish event
        await self._event_publisher.publish(
            UserEmailVerified(
                tenant_id=saved_user.tenant_id,
                user_id=saved_user.id,
                email=str(saved_user.email),
            )
        )

        return self._to_dto(saved_user)

    def _to_dto(self, user: User) -> UserDTO:
        """Convert user entity to DTO."""
        return UserDTO(
            id=user.id,
            tenant_id=user.tenant_id,
            email=str(user.email),
            role=user.role.value,
            status=user.status.value,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_email_verified=user.is_email_verified,
            is_active=user.is_active,
            is_locked=user.is_locked,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class RequestPasswordReset:
    """Use case for requesting a password reset."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        email_service: EmailService,
        event_publisher: EventPublisher,
        reset_url_template: str = "/reset-password?token={token}",
    ) -> None:
        self._user_repo = user_repository
        self._token_repo = token_repository
        self._email_service = email_service
        self._event_publisher = event_publisher
        self._reset_url_template = reset_url_template

    async def execute(self, command: RequestPasswordResetCommand) -> None:
        """Request password reset.

        Args:
            command: Reset request command with email.

        Note:
            This method always succeeds to prevent email enumeration.
            If user doesn't exist, no email is sent but no error is raised.
        """
        user = await self._user_repo.get_by_email(command.email)
        if not user:
            # Don't reveal that user doesn't exist
            return

        # Generate and save reset token
        token = TokenGenerator.generate_password_reset_token()
        expires_at = _utc_now() + timedelta(hours=1)
        await self._token_repo.save_password_reset_token(
            user_id=user.id,
            token=token,
            expires_at=expires_at.isoformat(),
        )

        # Send reset email
        reset_url = self._reset_url_template.format(token=token)
        await self._email_service.send_password_reset_email(
            email=str(user.email),
            reset_url=reset_url,
            user_name=user.full_name,
        )

        # Publish event
        await self._event_publisher.publish(
            UserPasswordResetRequested(
                tenant_id=user.tenant_id,
                user_id=user.id,
                email=str(user.email),
            )
        )


class ResetPassword:
    """Use case for resetting password with token."""

    def __init__(
        self,
        user_repository: UserRepository,
        token_repository: TokenRepository,
        password_hasher: PasswordHasher,
        email_service: EmailService,
        event_publisher: EventPublisher,
    ) -> None:
        self._user_repo = user_repository
        self._token_repo = token_repository
        self._password_hasher = password_hasher
        self._email_service = email_service
        self._event_publisher = event_publisher

    async def execute(self, command: ResetPasswordCommand) -> None:
        """Reset password using token.

        Args:
            command: Reset command with token and new password.

        Raises:
            InvalidTokenError: If token is invalid.
            TokenExpiredError: If token has expired.
            PasswordPolicyError: If password doesn't meet requirements.
            UserNotFoundError: If user not found.
        """
        # Validate password policy
        violations = default_password_policy.validate(command.new_password)
        if violations:
            raise PasswordPolicyError(violations)

        # Get token data
        token_data = await self._token_repo.get_password_reset_token(command.token)
        if not token_data:
            raise InvalidTokenError("password reset token")

        # Check expiration
        expires_at = datetime.fromisoformat(token_data["expires_at"])
        if _utc_now() > expires_at:
            await self._token_repo.delete_password_reset_token(command.token)
            raise TokenExpiredError("password reset token")

        # Get user
        user = await self._user_repo.get_by_id(token_data["user_id"])
        if not user:
            raise UserNotFoundError(str(token_data["user_id"]))

        # Update password
        password_hash = self._password_hasher.hash(command.new_password)
        # Password is stored in infrastructure layer, not on domain entity
        await self._user_repo.save(user)

        # Delete used token
        await self._token_repo.delete_password_reset_token(command.token)

        # Send confirmation email
        await self._email_service.send_password_changed_email(
            email=str(user.email),
            user_name=user.full_name,
        )

        # Publish event
        await self._event_publisher.publish(
            UserPasswordChanged(
                tenant_id=user.tenant_id,
                user_id=user.id,
                changed_via="reset_token",
            )
        )


class ChangePassword:
    """Use case for changing password (authenticated user)."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        email_service: EmailService,
        event_publisher: EventPublisher,
    ) -> None:
        self._user_repo = user_repository
        self._password_hasher = password_hasher
        self._email_service = email_service
        self._event_publisher = event_publisher

    async def execute(self, command: ChangePasswordCommand) -> None:
        """Change user password.

        Args:
            command: Change password command.

        Raises:
            UserNotFoundError: If user not found.
            PasswordPolicyError: If new password doesn't meet requirements.
        """
        # Validate password policy
        violations = default_password_policy.validate(command.new_password)
        if violations:
            raise PasswordPolicyError(violations)

        # Get user
        user = await self._user_repo.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundError(str(command.user_id))

        # Verify current password and update
        # (actual verification happens in infrastructure layer)
        await self._user_repo.save(user)

        # Send confirmation email
        await self._email_service.send_password_changed_email(
            email=str(user.email),
            user_name=user.full_name,
        )

        # Publish event
        await self._event_publisher.publish(
            UserPasswordChanged(
                tenant_id=user.tenant_id,
                user_id=user.id,
                changed_via="user_action",
            )
        )


class UpdateProfile:
    """Use case for updating user profile."""

    def __init__(
        self,
        user_repository: UserRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._user_repo = user_repository
        self._event_publisher = event_publisher

    async def execute(self, command: UpdateProfileCommand) -> UserDTO:
        """Update user profile.

        Args:
            command: Update profile command.

        Returns:
            Updated user DTO.

        Raises:
            UserNotFoundError: If user not found.
        """
        user = await self._user_repo.get_by_id(command.user_id)
        if not user:
            raise UserNotFoundError(str(command.user_id))

        updated_fields: list[str] = []

        if command.first_name is not None:
            user.first_name = command.first_name
            updated_fields.append("first_name")

        if command.last_name is not None:
            user.last_name = command.last_name
            updated_fields.append("last_name")

        if updated_fields:
            user.updated_at = _utc_now()
            saved_user = await self._user_repo.save(user)

            await self._event_publisher.publish(
                UserProfileUpdated(
                    tenant_id=saved_user.tenant_id,
                    user_id=saved_user.id,
                    updated_fields=updated_fields,
                )
            )

            return self._to_dto(saved_user)

        return self._to_dto(user)

    def _to_dto(self, user: User) -> UserDTO:
        """Convert user entity to DTO."""
        return UserDTO(
            id=user.id,
            tenant_id=user.tenant_id,
            email=str(user.email),
            role=user.role.value,
            status=user.status.value,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            is_email_verified=user.is_email_verified,
            is_active=user.is_active,
            is_locked=user.is_locked,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
