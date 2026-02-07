"""API URL configuration for Django Finance.

This module defines the API URL patterns organized by version.
"""

from django.urls import include, path

app_name = "api"

urlpatterns = [
    # Accounts module
    path("auth/", include("modules.accounts.interfaces.urls", namespace="accounts")),
    # Demo module
    path("demo/", include("modules.demo.interfaces.urls", namespace="demo")),
    # Finance module
    path("finance/", include("modules.finance.interfaces.urls", namespace="finance")),
    # Social finance module
    path("social/", include("modules.social.interfaces.urls", namespace="social")),
]
