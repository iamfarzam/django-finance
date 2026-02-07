"""Django app configuration for the social finance module."""

from django.apps import AppConfig


class SocialInfrastructureConfig(AppConfig):
    """Configuration for the social module infrastructure."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.social.infrastructure"
    label = "social"
    verbose_name = "Social Finance"

    def ready(self):
        """Run when the app is ready."""
        # Import signal handlers if needed
        pass
