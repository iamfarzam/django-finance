"""Django app configuration for notifications infrastructure."""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for the notifications app."""

    name = "modules.notifications.infrastructure"
    label = "notifications"
    verbose_name = "Notifications"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        """Register signal handlers when app is ready."""
        # Import signals to register them
        import modules.notifications.signals  # noqa: F401
