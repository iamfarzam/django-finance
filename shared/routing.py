"""WebSocket URL routing for Django Channels.

This module defines the WebSocket URL patterns for the application.
"""

from django.urls import path

from modules.demo.interfaces.consumers import NotificationConsumer, StatusConsumer
from shared.consumers import FinanceConsumer, SocialConsumer

# WebSocket URL patterns
websocket_urlpatterns = [
    # Demo consumers (for testing/development)
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/status/", StatusConsumer.as_asgi()),
    # Finance domain - real-time account and transaction updates
    path("ws/finance/", FinanceConsumer.as_asgi()),
    # Social finance domain - peer debts, group expenses, settlements
    path("ws/social/", SocialConsumer.as_asgi()),
]
