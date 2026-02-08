"""API URL configuration for Django Finance.

This module defines the API URL patterns organized by version.
"""

from django.urls import include, path

from modules.web.api_views import DashboardAPIView

app_name = "api"

urlpatterns = [
    # Dashboard API (aggregated endpoint for React frontend)
    path("dashboard/", DashboardAPIView.as_view(), name="dashboard"),
    # Accounts module
    path("auth/", include("modules.accounts.interfaces.urls", namespace="accounts")),
    # Demo module
    path("demo/", include("modules.demo.interfaces.urls", namespace="demo")),
    # Finance module
    path("finance/", include("modules.finance.interfaces.urls", namespace="finance")),
    # Social finance module
    path("social/", include("modules.social.interfaces.urls", namespace="social")),
    # Subscriptions module
    path("subscriptions/", include("modules.subscriptions.interfaces.urls", namespace="subscriptions")),
]
