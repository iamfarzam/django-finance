"""Custom middleware for Django Finance.

This module provides middleware for:
- Correlation ID tracking across requests
- Tenant context propagation
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import TYPE_CHECKING, Callable

from django.http import HttpRequest, HttpResponse

if TYPE_CHECKING:
    pass

# Context variables for request-scoped data
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
tenant_id_var: ContextVar[uuid.UUID | None] = ContextVar("tenant_id", default=None)


def get_correlation_id() -> str | None:
    """Get the current correlation ID.

    Returns:
        The correlation ID for the current request, or None if not set.
    """
    return correlation_id_var.get()


def get_tenant_id() -> uuid.UUID | None:
    """Get the current tenant ID.

    Returns:
        The tenant ID for the current request, or None if not set.
    """
    return tenant_id_var.get()


class CorrelationIdMiddleware:
    """Middleware to track correlation IDs across requests.

    Extracts correlation ID from the X-Correlation-ID header if present,
    otherwise generates a new UUID. The correlation ID is stored in a
    context variable and added to the response headers.

    Usage:
        Add to MIDDLEWARE in settings:
        'shared.middleware.CorrelationIdMiddleware'

    Example:
        # Access correlation ID anywhere in the request context
        from shared.middleware import get_correlation_id
        correlation_id = get_correlation_id()
    """

    HEADER_NAME = "X-Correlation-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The HTTP response with correlation ID header.
        """
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get(
            self.HEADER_NAME, str(uuid.uuid4())
        )

        # Store in context variable
        token = correlation_id_var.set(correlation_id)

        # Add to request for easy access
        request.correlation_id = correlation_id  # type: ignore[attr-defined]

        try:
            response = self.get_response(request)
            # Add correlation ID to response headers
            response[self.HEADER_NAME] = correlation_id
            return response
        finally:
            # Reset context variable
            correlation_id_var.reset(token)


class TenantContextMiddleware:
    """Middleware to establish tenant context for each request.

    For authenticated requests, extracts the tenant_id from:
    - JWT token claims (API requests)
    - Session (Web requests)

    The tenant ID is stored in a context variable and can be accessed
    anywhere in the request handling chain.

    Usage:
        Add to MIDDLEWARE in settings after AuthenticationMiddleware:
        'shared.middleware.TenantContextMiddleware'

    Example:
        # Access tenant ID anywhere in the request context
        from shared.middleware import get_tenant_id
        tenant_id = get_tenant_id()
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            The HTTP response.
        """
        tenant_id = self._extract_tenant_id(request)
        token = tenant_id_var.set(tenant_id)

        # Add to request for easy access
        request.tenant_id = tenant_id  # type: ignore[attr-defined]

        try:
            return self.get_response(request)
        finally:
            tenant_id_var.reset(token)

    def _extract_tenant_id(self, request: HttpRequest) -> uuid.UUID | None:
        """Extract tenant ID from the request.

        Priority:
        1. JWT token claim (for API requests)
        2. Session (for web requests)
        3. User's associated tenant (if user is authenticated)

        Args:
            request: The incoming HTTP request.

        Returns:
            The tenant UUID or None if not authenticated.
        """
        # Check if user is authenticated
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        # Try to get from JWT token claims (set by SimpleJWT)
        if hasattr(request, "auth") and request.auth:
            tenant_id = getattr(request.auth, "get", lambda x: None)("tenant_id")
            if tenant_id:
                try:
                    return uuid.UUID(str(tenant_id))
                except (ValueError, TypeError):
                    pass

        # Try to get from session
        if hasattr(request, "session"):
            tenant_id = request.session.get("tenant_id")
            if tenant_id:
                try:
                    return uuid.UUID(str(tenant_id))
                except (ValueError, TypeError):
                    pass

        # Try to get from user model (if it has tenant_id attribute)
        if hasattr(request.user, "tenant_id"):
            tenant_id = getattr(request.user, "tenant_id")
            if tenant_id:
                if isinstance(tenant_id, uuid.UUID):
                    return tenant_id
                try:
                    return uuid.UUID(str(tenant_id))
                except (ValueError, TypeError):
                    pass

        return None


class RequestLoggingMiddleware:
    """Middleware to log request information.

    Logs request start and completion with timing information.
    Uses structlog for structured logging with correlation ID.

    Usage:
        Add to MIDDLEWARE in settings:
        'shared.middleware.RequestLoggingMiddleware'
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request with logging.

        Args:
            request: The incoming HTTP request.

        Returns:
            The HTTP response.
        """
        import time

        import structlog

        logger = structlog.get_logger()

        # Skip health check endpoints to avoid log spam
        if request.path in ("/health/", "/health/ready/"):
            return self.get_response(request)

        start_time = time.monotonic()

        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.path,
            correlation_id=get_correlation_id(),
            tenant_id=str(get_tenant_id()) if get_tenant_id() else None,
        )

        response = self.get_response(request)

        # Calculate duration
        duration_ms = (time.monotonic() - start_time) * 1000

        # Log request completion
        logger.info(
            "request_completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            correlation_id=get_correlation_id(),
            tenant_id=str(get_tenant_id()) if get_tenant_id() else None,
        )

        return response
