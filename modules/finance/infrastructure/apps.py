"""Django app configuration for finance infrastructure."""

from django.apps import AppConfig


class FinanceInfrastructureConfig(AppConfig):
    """Configuration for the finance infrastructure app."""

    name = "modules.finance.infrastructure"
    label = "finance"
    verbose_name = "Finance"
    default_auto_field = "django.db.models.BigAutoField"
