"""ASGI config for Django Finance project.

This module exposes the ASGI callable as a module-level variable named ``application``.
It supports both HTTP and WebSocket protocols using Django Channels.

For more information on this file, see:
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
https://channels.readthedocs.io/en/stable/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import websocket URL patterns after Django setup
from shared.routing import websocket_urlpatterns  # noqa: E402


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        ),
    }
)
