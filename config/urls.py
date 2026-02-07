"""Root URL configuration for Django Finance.

The `urlpatterns` list routes URLs to views.
"""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from shared.views import health_check, health_ready

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Health checks
    path("health/", health_check, name="health-check"),
    path("health/ready/", health_ready, name="health-ready"),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="api-schema"),
        name="api-redoc",
    ),
    # API v1
    path("api/v1/", include("shared.api_urls", namespace="api-v1")),
]

# Debug toolbar in development
if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Admin site customization
admin.site.site_header = "Django Finance Administration"
admin.site.site_title = "Django Finance Admin"
admin.site.index_title = "Welcome to Django Finance Administration"
