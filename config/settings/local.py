"""Local development settings.

These settings are for local development only.
Never use in production.
"""

from config.env import settings as env
from config.settings.base import *  # noqa: F401, F403

# =============================================================================
# Debug Settings
# =============================================================================

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]  # noqa: S104

# =============================================================================
# Debug Toolbar
# =============================================================================

if env.enable_debug_toolbar:
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1"]
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
    }

# =============================================================================
# Email
# =============================================================================

# Use console backend for local development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# =============================================================================
# REST Framework
# =============================================================================

# Add browsable API in development
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
]

# =============================================================================
# CORS (Allow all in development)
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# Logging (More verbose in development)
# =============================================================================

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"  # noqa: F405

# =============================================================================
# Session (No secure cookies in development)
# =============================================================================

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# =============================================================================
# Security (Relaxed for development)
# =============================================================================

SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
