"""Repository and service interfaces for the accounts module.

These abstract base classes define contracts that infrastructure
implementations must fulfill.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from modules.accounts.domain.entities import User


class UserRepository(ABC):
    """Abstract repository for User persistence."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            User if found, None otherwise.
        """
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: The user's email.

        Returns:
            User if found, None otherwise.
        """
        ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if a user with the given email exists.

        Args:
            email: The email to check.

        Returns:
            True if user exists, False otherwise.
        """
        ...

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save a user (create or update).

        Args:
            user: The user to save.

        Returns:
            The saved user with any generated fields.
        """
        ...

    @abstractmethod
    async def delete(self, user_id: UUID) -> None:
        """Hard delete a user.

        Args:
            user_id: The user's UUID.
        """
        ...


class TokenRepository(ABC):
    """Abstract repository for token persistence."""

    @abstractmethod
    async def save_verification_token(
        self, user_id: UUID, email: str, token: str, expires_at: str
    ) -> None:
        """Save an email verification token.

        Args:
            user_id: The user's UUID.
            email: The email to verify.
            token: The verification token.
            expires_at: Token expiration datetime.
        """
        ...

    @abstractmethod
    async def get_verification_token(self, token: str) -> dict | None:
        """Get verification token data.

        Args:
            token: The verification token.

        Returns:
            Token data dict if found and valid, None otherwise.
        """
        ...

    @abstractmethod
    async def delete_verification_token(self, token: str) -> None:
        """Delete a verification token.

        Args:
            token: The verification token.
        """
        ...

    @abstractmethod
    async def save_password_reset_token(
        self, user_id: UUID, token: str, expires_at: str
    ) -> None:
        """Save a password reset token.

        Args:
            user_id: The user's UUID.
            token: The reset token.
            expires_at: Token expiration datetime.
        """
        ...

    @abstractmethod
    async def get_password_reset_token(self, token: str) -> dict | None:
        """Get password reset token data.

        Args:
            token: The reset token.

        Returns:
            Token data dict if found and valid, None otherwise.
        """
        ...

    @abstractmethod
    async def delete_password_reset_token(self, token: str) -> None:
        """Delete a password reset token.

        Args:
            token: The reset token.
        """
        ...


class PasswordHasher(ABC):
    """Abstract service for password hashing."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a password.

        Args:
            password: The plaintext password.

        Returns:
            The hashed password.
        """
        ...

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Verify a password against a hash.

        Args:
            password: The plaintext password.
            password_hash: The hashed password.

        Returns:
            True if password matches, False otherwise.
        """
        ...


class EmailService(ABC):
    """Abstract service for sending emails."""

    @abstractmethod
    async def send_verification_email(
        self, email: str, verification_url: str, user_name: str
    ) -> None:
        """Send email verification email.

        Args:
            email: Recipient email address.
            verification_url: URL for email verification.
            user_name: User's display name.
        """
        ...

    @abstractmethod
    async def send_password_reset_email(
        self, email: str, reset_url: str, user_name: str
    ) -> None:
        """Send password reset email.

        Args:
            email: Recipient email address.
            reset_url: URL for password reset.
            user_name: User's display name.
        """
        ...

    @abstractmethod
    async def send_password_changed_email(self, email: str, user_name: str) -> None:
        """Send password changed notification email.

        Args:
            email: Recipient email address.
            user_name: User's display name.
        """
        ...


class EventPublisher(ABC):
    """Abstract service for publishing domain events."""

    @abstractmethod
    async def publish(self, event: object) -> None:
        """Publish a domain event.

        Args:
            event: The domain event to publish.
        """
        ...
