"""Django app configuration for demo module."""

from django.apps import AppConfig


class DemoConfig(AppConfig):
    """Configuration for the demo app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.demo.infrastructure"
    label = "demo"
    verbose_name = "Demo Module"
