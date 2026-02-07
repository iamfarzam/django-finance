"""WebSocket URL routing for Django Channels.

This module defines the WebSocket URL patterns for the application.
"""

from django.urls import path

from modules.demo.interfaces.consumers import NotificationConsumer, StatusConsumer

# WebSocket URL patterns
websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
    path("ws/status/", StatusConsumer.as_asgi()),
]
