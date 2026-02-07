"""Custom authentication backends for the accounts module.

Provides email-based authentication for the custom User model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

if TYPE_CHECKING:
    from django.http import HttpRequest

    from modules.accounts.infrastructure.models import User


class EmailBackend(ModelBackend):
    """Authentication backend that uses email instead of username.

    This backend is required because our User model uses email as the
    USERNAME_FIELD. Django's default ModelBackend looks for a 'username'
    credential, but we want to authenticate with 'email'.

    Usage:
        Add to AUTHENTICATION_BACKENDS in settings:
        AUTHENTICATION_BACKENDS = [
            'modules.accounts.infrastructure.backends.EmailBackend',
        ]

    Example:
        from django.contrib.auth import authenticate
        user = authenticate(request, email='user@example.com', password='password')
    """

    def authenticate(
        self,
        request: HttpRequest | None,
        email: str | None = None,
        password: str | None = None,
        **kwargs: Any,
    ) -> "User | None":
        """Authenticate a user by email and password.

        Args:
            request: The current request (may be None).
            email: The user's email address.
            password: The user's password.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            The authenticated User if credentials are valid, None otherwise.
        """
        if email is None or password is None:
            return None

        UserModel = get_user_model()

        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user.
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def get_user(self, user_id: int) -> "User | None":
        """Get a user by primary key.

        Args:
            user_id: The user's primary key.

        Returns:
            The User if found and active, None otherwise.
        """
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

        return user if self.user_can_authenticate(user) else None
