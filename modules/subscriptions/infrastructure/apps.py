"""Django app configuration for subscriptions module."""

from django.apps import AppConfig


class SubscriptionsConfig(AppConfig):
    """Configuration for the subscriptions module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.subscriptions.infrastructure"
    label = "subscriptions"
    verbose_name = "Subscriptions"

    def ready(self) -> None:
        """Run when the app is ready."""
        pass
