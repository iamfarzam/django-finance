"""URL configuration for subscriptions module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.subscriptions.interfaces.views import SubscriptionViewSet

app_name = "subscriptions"

router = DefaultRouter()
router.register(r"", SubscriptionViewSet, basename="subscription")

urlpatterns = [
    path("", include(router.urls)),
]
