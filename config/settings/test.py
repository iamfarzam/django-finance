"""Test environment settings.

These settings are optimized for fast test execution.
"""

from config.settings.base import *  # noqa: F401, F403

# =============================================================================
# Debug Settings
# =============================================================================

DEBUG = False
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# =============================================================================
# Database (In-memory or faster test DB)
# =============================================================================

# Use same database but with optimizations
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405

# =============================================================================
# Password Hashing (Fast hasher for tests)
# =============================================================================

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# =============================================================================
# Email
# =============================================================================

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# =============================================================================
# Celery (Eager execution for tests)
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# =============================================================================
# Cache (Local memory for tests)
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

# =============================================================================
# Channels (In-memory layer for tests)
# =============================================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# =============================================================================
# Logging (Minimal logging in tests)
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# =============================================================================
# Security (Disabled for tests)
# =============================================================================

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# =============================================================================
# REST Framework (Disable throttling for tests)
# =============================================================================

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {}  # noqa: F405
