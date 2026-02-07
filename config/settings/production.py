"""Production settings.

These settings are for production deployment only.
Security and performance are prioritized.
"""

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from config.env import settings as env
from config.settings.base import *  # noqa: F401, F403

# =============================================================================
# Debug Settings
# =============================================================================

DEBUG = False

# =============================================================================
# Security Settings
# =============================================================================

# HTTPS/SSL
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Type Sniffing
SECURE_CONTENT_TYPE_NOSNIFF = True

# XSS Protection
SECURE_BROWSER_XSS_FILTER = True

# Cookies
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Clickjacking protection
X_FRAME_OPTIONS = "DENY"

# =============================================================================
# Database (Production optimizations)
# =============================================================================

DATABASES["default"]["CONN_MAX_AGE"] = 600  # noqa: F405
DATABASES["default"]["OPTIONS"]["sslmode"] = "require"  # noqa: F405

# =============================================================================
# Logging (JSON format for production)
# =============================================================================

LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405
LOGGING["loggers"]["django"]["handlers"] = ["json"]  # noqa: F405
LOGGING["loggers"]["celery"]["handlers"] = ["json"]  # noqa: F405
LOGGING["loggers"]["modules"]["handlers"] = ["json"]  # noqa: F405

# =============================================================================
# Sentry Error Tracking
# =============================================================================

if env.sentry_dsn:
    sentry_sdk.init(
        dsn=env.sentry_dsn,
        integrations=[
            DjangoIntegration(
                transaction_style="url",
                middleware_spans=True,
            ),
            CeleryIntegration(
                monitor_beat_tasks=True,
            ),
            RedisIntegration(),
            LoggingIntegration(
                level=None,
                event_level=None,
            ),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=0.1,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        profiles_sample_rate=0.1,
        # Send user info
        send_default_pii=False,
        # Environment
        environment="production",
        # Release tracking
        release=None,  # Set via CI/CD
    )

# =============================================================================
# Static Files (Production)
# =============================================================================

# Consider using whitenoise or a CDN
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

# =============================================================================
# REST Framework (Production)
# =============================================================================

# Only JSON renderer in production
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
]

# Stricter throttling for production
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "60/hour",
    "user": "1000/hour",
}
