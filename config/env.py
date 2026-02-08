"""Environment configuration using pydantic-settings.

This module provides typed environment variable configuration with validation.
All environment variables are loaded and validated at application startup.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings are validated at startup. Missing required settings
    will raise a validation error with clear messaging.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["local", "test", "production"] = Field(
        default="local",
        alias="DJANGO_ENVIRONMENT",
        description="Deployment environment",
    )

    # Django Core
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(alias="SECRET_KEY")
    allowed_hosts: list[str] = Field(default=["localhost", "127.0.0.1"])
    site_url: str = Field(default="http://localhost:8000", alias="SITE_URL")

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated string to list."""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",") if host.strip()]
        return v

    # Database
    database_url: PostgresDsn = Field(alias="DATABASE_URL")

    # Redis
    redis_url: RedisDsn = Field(alias="REDIS_URL")
    cache_url: RedisDsn | None = Field(default=None, alias="CACHE_URL")

    # JWT Authentication
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_access_lifetime_minutes: int = Field(
        default=15, alias="JWT_ACCESS_LIFETIME_MINUTES"
    )
    jwt_refresh_lifetime_days: int = Field(default=7, alias="JWT_REFRESH_LIFETIME_DAYS")

    # Email
    email_backend: str = Field(
        default="django.core.mail.backends.console.EmailBackend",
        alias="EMAIL_BACKEND",
    )
    email_host: str = Field(default="smtp.example.com", alias="EMAIL_HOST")
    email_port: int = Field(default=587, alias="EMAIL_PORT")
    email_use_tls: bool = Field(default=True, alias="EMAIL_USE_TLS")
    email_host_user: str = Field(default="", alias="EMAIL_HOST_USER")
    email_host_password: str = Field(default="", alias="EMAIL_HOST_PASSWORD")
    default_from_email: str = Field(
        default="noreply@example.com", alias="DEFAULT_FROM_EMAIL"
    )

    # Security
    csrf_trusted_origins: list[str] = Field(default_factory=list)
    cors_allowed_origins: list[str] = Field(default_factory=list)

    @field_validator("csrf_trusted_origins", "cors_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated string to list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # Observability
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )

    # Celery
    celery_broker_url: RedisDsn | None = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: RedisDsn | None = Field(
        default=None, alias="CELERY_RESULT_BACKEND"
    )

    # Feature Flags
    feature_mfa_enabled: bool = Field(default=False, alias="FEATURE_MFA_ENABLED")

    # Development
    enable_debug_toolbar: bool = Field(default=False, alias="ENABLE_DEBUG_TOOLBAR")

    @property
    def effective_cache_url(self) -> str:
        """Return cache URL, defaulting to Redis URL."""
        return str(self.cache_url or self.redis_url)

    @property
    def effective_celery_broker_url(self) -> str:
        """Return Celery broker URL, defaulting to Redis URL."""
        return str(self.celery_broker_url or self.redis_url)

    @property
    def effective_celery_result_backend(self) -> str:
        """Return Celery result backend, defaulting to Redis URL."""
        return str(self.celery_result_backend or self.redis_url)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are loaded once and cached for performance.
    Use this function to access settings throughout the application.

    Returns:
        Validated Settings instance.
    """
    return Settings()  # type: ignore[call-arg]


# Export settings instance for convenience
settings = get_settings()
