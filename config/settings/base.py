"""Base Django settings shared across all environments.

Do not import this module directly. Use config.settings instead.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from config.env import settings as env

# =============================================================================
# Core Settings
# =============================================================================

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env.secret_key
DEBUG = env.debug
ALLOWED_HOSTS = env.allowed_hosts

# Site configuration
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
SITE_URL = env.site_url

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "accounts.User"

# =============================================================================
# Application Definition
# =============================================================================

DJANGO_APPS = [
    "daphne",  # Must be before staticfiles for ASGI
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

THIRD_PARTY_APPS = [
    # REST Framework
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    # CORS
    "corsheaders",
    # Channels
    "channels",
    # Celery
    "django_celery_beat",
    "django_celery_results",
]

PROJECT_APPS = [
    # Shared utilities
    "shared",
    # Feature modules (infrastructure layer for Django)
    "modules.accounts.infrastructure",
    "modules.demo.infrastructure",
    "modules.finance.infrastructure",
    "modules.social.infrastructure",
    "modules.subscriptions.infrastructure",
    # "modules.notifications.infrastructure",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + PROJECT_APPS

# =============================================================================
# Middleware
# =============================================================================

MIDDLEWARE = [
    # Security first
    "django.middleware.security.SecurityMiddleware",
    # CORS headers
    "corsheaders.middleware.CorsMiddleware",
    # Django defaults
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware
    "shared.middleware.CorrelationIdMiddleware",
    "shared.middleware.TenantContextMiddleware",
    "shared.middleware.SubscriptionContextMiddleware",
    "shared.middleware.UsageTrackingMiddleware",
    "shared.middleware.AuditLoggingMiddleware",
]

# =============================================================================
# Database
# =============================================================================

# Parse database URL (Pydantic 2.x MultiHostUrl format)
_db_hosts = env.database_url.hosts()
_db_host = _db_hosts[0] if _db_hosts else {}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.database_url.path.lstrip("/") if env.database_url.path else "",
        "USER": _db_host.get("username") or "",
        "PASSWORD": _db_host.get("password") or "",
        "HOST": _db_host.get("host") or "localhost",
        "PORT": _db_host.get("port") or 5432,
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# =============================================================================
# Cache
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env.effective_cache_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 50,
        },
        "KEY_PREFIX": "dj_finance",
    }
}

# =============================================================================
# Channels (WebSocket)
# =============================================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [str(env.redis_url)],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}

# =============================================================================
# Authentication Backends
# =============================================================================

AUTHENTICATION_BACKENDS = [
    "modules.accounts.infrastructure.backends.EmailBackend",
]

# =============================================================================
# Password Validation
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 12,  # Baseline: 12 character minimum
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Password hashers - Argon2id first (per baseline)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

# =============================================================================
# Internationalization
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Locale paths for translations
LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# =============================================================================
# Static & Media Files
# =============================================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# Templates
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =============================================================================
# Email
# =============================================================================

EMAIL_BACKEND = env.email_backend
EMAIL_HOST = env.email_host
EMAIL_PORT = env.email_port
EMAIL_USE_TLS = env.email_use_tls
EMAIL_HOST_USER = env.email_host_user
EMAIL_HOST_PASSWORD = env.email_host_password
DEFAULT_FROM_EMAIL = env.default_from_email

# =============================================================================
# REST Framework
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
        "login": "5/minute",
        "password_reset": "3/hour",
        "register": "10/hour",
        "verify_email": "10/minute",
        "change_password": "5/hour",
        "resend_verification": "3/hour",
        # Finance API throttle rates
        "finance_user": "200/hour",
        "transaction_create": "100/hour",
        "transfer_create": "50/hour",
        "account_create": "10/hour",
        "report_generate": "30/hour",
        "bulk_operation": "10/hour",
        "premium_finance": "1000/hour",
        "finance_write": "100/hour",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "shared.exceptions.custom_exception_handler",
}

# =============================================================================
# JWT Settings
# =============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.jwt_access_lifetime_minutes),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.jwt_refresh_lifetime_days),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": env.jwt_secret_key,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "TOKEN_TYPE_CLAIM": "token_type",
    # Custom claims for multi-tenancy
    "TOKEN_OBTAIN_SERIALIZER": "modules.accounts.interfaces.serializers.CustomTokenObtainPairSerializer",
}

# =============================================================================
# drf-spectacular (OpenAPI)
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Django Finance API",
    "DESCRIPTION": """
# Django Finance API

A comprehensive finance management platform API for tracking:
- **Cash Flow**: Income and expenses across multiple accounts
- **Accounts**: Bank accounts, credit cards, cash, investments
- **Transactions**: Credits, debits, and transfers
- **Assets**: Real estate, vehicles, investments, collectibles
- **Liabilities**: Credit cards, mortgages, loans
- **Net Worth**: Calculated from all financial data

## Authentication

This API uses JWT (JSON Web Token) for authentication.

1. Obtain tokens via `POST /api/v1/auth/token/`
2. Include the access token in the `Authorization` header:
   ```
   Authorization: Bearer <access_token>
   ```
3. Refresh tokens via `POST /api/v1/auth/token/refresh/`

## Rate Limiting

- Anonymous: 100 requests/hour
- Authenticated users: 1000 requests/hour
- Premium users: Higher limits on finance endpoints

## Multi-Tenancy

All financial data is tenant-scoped. Each user has their own tenant,
and data is automatically isolated per tenant.

## Currencies

Supported currencies: USD, EUR, GBP, CAD, AUD, JPY, INR
""",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v[0-9]",
    "COMPONENT_SPLIT_REQUEST": True,
    # Security scheme for JWT
    "SECURITY": [{"Bearer": []}],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "Bearer": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT access token obtained from /api/v1/auth/token/",
            }
        }
    },
    # Tags for organizing endpoints
    "TAGS": [
        {"name": "Authentication", "description": "User authentication and token management"},
        {"name": "Accounts", "description": "Bank accounts, wallets, and account management"},
        {"name": "Transactions", "description": "Income, expenses, and transaction management"},
        {"name": "Transfers", "description": "Money transfers between accounts"},
        {"name": "Assets", "description": "Asset tracking and valuation"},
        {"name": "Liabilities", "description": "Debt and liability management"},
        {"name": "Loans", "description": "Loan tracking and payment management"},
        {"name": "Categories", "description": "Transaction categorization"},
        {"name": "Reports", "description": "Financial reports and analytics"},
        {"name": "Social - Contacts", "description": "Friends and contacts management"},
        {"name": "Social - Contact Groups", "description": "Contact group management"},
        {"name": "Social - Peer Debts", "description": "Money lent/borrowed between peers"},
        {"name": "Social - Expense Groups", "description": "Group expense splitting setup"},
        {"name": "Social - Group Expenses", "description": "Shared expenses with automatic splitting"},
        {"name": "Social - Settlements", "description": "Debt settlement records"},
        {"name": "Social - Balances", "description": "Balance calculations and suggestions"},
    ],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
    "REDOC_UI_SETTINGS": {
        "hideDownloadButton": False,
        "disableSearch": False,
    },
    # External documentation
    "EXTERNAL_DOCS": {
        "description": "Project Documentation",
        "url": "https://github.com/your-org/django-finance",
    },
    # Contact information
    "CONTACT": {
        "name": "Django Finance Support",
        "email": "support@djangofinance.dev",
    },
    # License
    "LICENSE": {
        "name": "MIT",
    },
    # Preprocessing hooks
    "PREPROCESSING_HOOKS": [],
    "POSTPROCESSING_HOOKS": [],
}

# =============================================================================
# CORS Settings
# =============================================================================

CORS_ALLOWED_ORIGINS = env.cors_allowed_origins
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# CSRF Settings
# =============================================================================

CSRF_TRUSTED_ORIGINS = env.csrf_trusted_origins

# =============================================================================
# Session Settings
# =============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 2 weeks
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# =============================================================================
# Celery Configuration
# =============================================================================

CELERY_BROKER_URL = env.effective_celery_broker_url
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "default"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Periodic tasks (can also be configured via Django admin)
CELERY_BEAT_SCHEDULE = {
    "process-outbox-every-30-seconds": {
        "task": "demo.process_outbox",
        "schedule": 30.0,  # Every 30 seconds
    },
    "cleanup-outbox-daily": {
        "task": "demo.cleanup_processed_outbox",
        "schedule": 86400.0,  # Every 24 hours
        "kwargs": {"days_old": 7},
    },
}

# Task retry settings
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# =============================================================================
# Logging Configuration
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "shared.logging.StructlogFormatter",
        },
        "console": {
            "format": "%(levelname)s %(asctime)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "json": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env.log_level,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "modules": {
            "handlers": ["console"],
            "level": env.log_level,
            "propagate": False,
        },
    },
}
