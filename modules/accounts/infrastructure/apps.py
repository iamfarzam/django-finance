"""Django app configuration for accounts module."""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.accounts.infrastructure"
    label = "accounts"
    verbose_name = "User Accounts"

    def ready(self) -> None:
        """Import signal handlers when app is ready."""
        # Import signals to register handlers
        pass
