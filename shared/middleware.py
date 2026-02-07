"""Custom middleware for Django Finance.

This module provides middleware for:
- Correlation ID tracking across requests
- Tenant context propagation
- Request logging
- Audit logging for API operations
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from typing import TYPE_CHECKING, Callable

from django.http import HttpRequest, HttpResponse

# Context variables for request-scoped data
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)
tenant_id_var: ContextVar[uuid.UUID | None] = ContextVar("tenant_id", default=None)
subscription_context_var: ContextVar["PermissionContext | None"] = ContextVar(
    "subscription_context", default=None
)

if TYPE_CHECKING:
    from modules.subscriptions.domain.services import PermissionContext


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


def get_subscription_context() -> "PermissionContext | None":
    """Get the current subscription context.

    Returns:
        The PermissionContext for the current request, or None if not set.
    """
    return subscription_context_var.get()


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


class SubscriptionContextMiddleware:
    """Middleware to attach subscription context to each request.

    For authenticated requests, loads the user's subscription permissions
    and makes them available throughout the request handling chain.

    Usage:
        Add to MIDDLEWARE in settings after TenantContextMiddleware:
        'shared.middleware.SubscriptionContextMiddleware'

    Example:
        # Access subscription context anywhere in the request context
        from shared.middleware import get_subscription_context
        context = get_subscription_context()
        if context and context.has_feature("reports.advanced"):
            # Show advanced features
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
        context = self._get_subscription_context(request)
        token = subscription_context_var.set(context)

        # Add to request for easy access
        request.subscription_context = context  # type: ignore[attr-defined]

        try:
            return self.get_response(request)
        finally:
            subscription_context_var.reset(token)

    def _get_subscription_context(
        self, request: HttpRequest
    ) -> "PermissionContext | None":
        """Get subscription context for the request.

        Args:
            request: The incoming HTTP request.

        Returns:
            PermissionContext or None if not authenticated.
        """
        # Only load context for authenticated users
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        try:
            from modules.subscriptions.domain.services import PermissionService

            return PermissionService.get_user_context(request.user)
        except Exception:
            # If subscription system fails, return None
            # This allows the app to function even if subscriptions are broken
            return None


class UsageTrackingMiddleware:
    """Middleware to track API usage for rate limiting.

    Tracks API calls for users with API access limits.
    Only tracks authenticated API requests (not web/session requests).

    Usage:
        Add to MIDDLEWARE in settings after SubscriptionContextMiddleware:
        'shared.middleware.UsageTrackingMiddleware'
    """

    # Paths to track usage for
    TRACKED_PATH_PREFIXES = (
        "/api/v1/",
    )

    # Paths to exclude from tracking
    EXCLUDED_PATHS = (
        "/api/v1/auth/token/",
        "/api/v1/auth/token/refresh/",
        "/api/v1/subscriptions/",
    )

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
        # Process the request first
        response = self.get_response(request)

        # Only track successful API requests
        if response.status_code < 400 and self._should_track(request):
            self._track_usage(request)

        return response

    def _should_track(self, request: HttpRequest) -> bool:
        """Check if request should be tracked.

        Args:
            request: The HTTP request.

        Returns:
            True if request should be tracked.
        """
        # Only track authenticated users
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return False

        # Check if it's an API path
        if not any(
            request.path.startswith(prefix)
            for prefix in self.TRACKED_PATH_PREFIXES
        ):
            return False

        # Exclude certain paths
        if any(
            request.path.startswith(path)
            for path in self.EXCLUDED_PATHS
        ):
            return False

        # Only track JWT-authenticated requests (not session-based)
        # Session-based requests are web UI and should not count against API limits
        if hasattr(request, "auth") and request.auth:
            return True

        return False

    def _track_usage(self, request: HttpRequest) -> None:
        """Track API usage for the request.

        Args:
            request: The HTTP request.
        """
        try:
            from modules.subscriptions.domain.enums import UsageType
            from modules.subscriptions.domain.services import UsageLimitService

            UsageLimitService.increment_usage(
                request.user,
                UsageType.API_CALLS_DAILY.value,
            )
        except Exception:
            # Don't fail the request if usage tracking fails
            import structlog

            logger = structlog.get_logger()
            logger.warning(
                "usage_tracking_failed",
                user_id=str(getattr(request.user, "id", None)),
                path=request.path,
            )


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


class AuditLoggingMiddleware:
    """Middleware to log API operations for audit trail.

    This middleware automatically logs write operations (POST, PUT, PATCH, DELETE)
    on finance-related endpoints. It captures:
    - The action performed
    - User and tenant context
    - Request details
    - Response status

    Usage:
        Add to MIDDLEWARE in settings:
        'shared.middleware.AuditLoggingMiddleware'
    """

    # Paths to audit (finance operations)
    AUDITABLE_PATH_PREFIXES = (
        "/api/v1/finance/",
        "/api/v1/accounts/",
        "/api/v1/auth/",
        "/api/v1/subscriptions/",
    )

    # Methods that trigger audit logging
    AUDITABLE_METHODS = ("POST", "PUT", "PATCH", "DELETE")

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        """Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request with audit logging.

        Args:
            request: The incoming HTTP request.

        Returns:
            The HTTP response.
        """
        # Skip if not an auditable request
        if not self._should_audit(request):
            return self.get_response(request)

        import structlog

        from shared.audit import AuditAction, audit_logger

        logger = structlog.get_logger()

        # Process the request
        response = self.get_response(request)

        # Log audit event for successful write operations
        if response.status_code < 400:
            try:
                self._log_audit_event(request, response)
            except Exception as e:
                logger.warning(
                    "audit_logging_failed",
                    error=str(e),
                    path=request.path,
                    method=request.method,
                )

        return response

    def _should_audit(self, request: HttpRequest) -> bool:
        """Check if request should be audited.

        Args:
            request: The HTTP request.

        Returns:
            True if request should be audited.
        """
        # Only audit write methods
        if request.method not in self.AUDITABLE_METHODS:
            return False

        # Only audit specific paths
        return any(
            request.path.startswith(prefix)
            for prefix in self.AUDITABLE_PATH_PREFIXES
        )

    def _log_audit_event(
        self, request: HttpRequest, response: HttpResponse
    ) -> None:
        """Log audit event for the request.

        Args:
            request: The HTTP request.
            response: The HTTP response.
        """
        from shared.audit import AuditAction, audit_logger

        # Determine action from request
        action = self._determine_action(request)
        if not action:
            return

        # Get user info
        user_id = None
        tenant_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = getattr(request.user, "id", None)
            tenant_id = getattr(request.user, "tenant_id", None)

        # Extract resource info from path
        resource_type, resource_id = self._extract_resource_info(request.path)

        # Log the event
        audit_logger.log_action(
            action=action,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            details={
                "response_status": response.status_code,
                "method": request.method,
            },
        )

    def _determine_action(self, request: HttpRequest) -> "AuditAction | None":
        """Determine audit action from request.

        Args:
            request: The HTTP request.

        Returns:
            Appropriate AuditAction or None.
        """
        from shared.audit import AuditAction

        path = request.path.lower()
        method = request.method

        # Finance actions
        if "/accounts/" in path:
            if method == "POST":
                if "/close" in path:
                    return AuditAction.ACCOUNT_CLOSE
                if "/reopen" in path:
                    return AuditAction.ACCOUNT_REOPEN
                return AuditAction.ACCOUNT_CREATE
            if method in ("PUT", "PATCH"):
                return AuditAction.ACCOUNT_UPDATE
            if method == "DELETE":
                return AuditAction.ACCOUNT_DELETE

        if "/transactions/" in path:
            if method == "POST":
                if "/post" in path:
                    return AuditAction.TRANSACTION_POST
                if "/void" in path:
                    return AuditAction.TRANSACTION_VOID
                return AuditAction.TRANSACTION_CREATE

        if "/transfers/" in path:
            if method == "POST":
                return AuditAction.TRANSFER_CREATE

        if "/assets/" in path:
            if method == "POST":
                if "/update-value" in path:
                    return AuditAction.ASSET_VALUE_UPDATE
                return AuditAction.ASSET_CREATE
            if method in ("PUT", "PATCH"):
                return AuditAction.ASSET_UPDATE
            if method == "DELETE":
                return AuditAction.ASSET_DELETE

        if "/liabilities/" in path:
            if method == "POST":
                return AuditAction.LIABILITY_CREATE
            if method in ("PUT", "PATCH"):
                return AuditAction.LIABILITY_UPDATE
            if method == "DELETE":
                return AuditAction.LIABILITY_DELETE

        if "/loans/" in path:
            if method == "POST":
                if "/record-payment" in path:
                    return AuditAction.LOAN_PAYMENT
                return AuditAction.LOAN_CREATE
            if method in ("PUT", "PATCH"):
                return AuditAction.LOAN_UPDATE
            if method == "DELETE":
                return AuditAction.LOAN_DELETE

        # Auth actions
        if "/auth/" in path:
            if "/login" in path or "/token" in path:
                return AuditAction.USER_LOGIN
            if "/logout" in path:
                return AuditAction.USER_LOGOUT
            if "/password" in path:
                if "reset" in path:
                    return AuditAction.USER_PASSWORD_RESET
                return AuditAction.USER_PASSWORD_CHANGE
            if "/verify" in path:
                return AuditAction.USER_EMAIL_VERIFY

        return None

    def _extract_resource_info(self, path: str) -> tuple[str, str | None]:
        """Extract resource type and ID from path.

        Args:
            path: Request path.

        Returns:
            Tuple of (resource_type, resource_id).
        """
        parts = path.strip("/").split("/")

        # Find resource type and ID
        resource_type = "unknown"
        resource_id = None

        for i, part in enumerate(parts):
            if part in (
                "accounts",
                "transactions",
                "transfers",
                "assets",
                "liabilities",
                "loans",
                "categories",
            ):
                resource_type = part.rstrip("s")  # Singularize
                # Check if next part is a UUID
                if i + 1 < len(parts):
                    next_part = parts[i + 1]
                    try:
                        uuid.UUID(next_part)
                        resource_id = next_part
                    except ValueError:
                        pass
                break

        return resource_type, resource_id
