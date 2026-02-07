"""Domain services for the accounts module.

These services contain domain logic that doesn't belong to a single entity.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass


@dataclass
class PasswordPolicy:
    """Password policy configuration.

    Defines the rules for password validation based on baseline requirements.
    """

    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_digit: bool = True
    require_special: bool = True
    special_characters: str = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def validate(self, password: str) -> list[str]:
        """Validate password against policy.

        Args:
            password: The password to validate.

        Returns:
            List of policy violations (empty if valid).
        """
        violations: list[str] = []

        if len(password) < self.min_length:
            violations.append(
                f"Password must be at least {self.min_length} characters long"
            )

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            violations.append("Password must contain at least one uppercase letter")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            violations.append("Password must contain at least one lowercase letter")

        if self.require_digit and not re.search(r"\d", password):
            violations.append("Password must contain at least one digit")

        if self.require_special:
            escaped_chars = re.escape(self.special_characters)
            if not re.search(f"[{escaped_chars}]", password):
                violations.append("Password must contain at least one special character")

        return violations

    def is_valid(self, password: str) -> bool:
        """Check if password meets policy requirements.

        Args:
            password: The password to check.

        Returns:
            True if password is valid, False otherwise.
        """
        return len(self.validate(password)) == 0


class TokenGenerator:
    """Service for generating secure tokens."""

    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure email verification token.

        Returns:
            URL-safe token string (64 characters).
        """
        return secrets.token_urlsafe(48)

    @staticmethod
    def generate_password_reset_token() -> str:
        """Generate a secure password reset token.

        Returns:
            URL-safe token string (64 characters).
        """
        return secrets.token_urlsafe(48)

    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token.

        Returns:
            URL-safe token string (32 characters).
        """
        return secrets.token_urlsafe(24)


# Default password policy based on baseline requirements
default_password_policy = PasswordPolicy(
    min_length=12,
    require_uppercase=True,
    require_lowercase=True,
    require_digit=True,
    require_special=True,
)
