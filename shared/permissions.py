"""DRF permission classes for the Django Finance platform.

This module provides role-based permission classes for API access control.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import permissions

if TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class IsActiveUser(permissions.BasePermission):
    """Permission to check if user is active and verified.

    Requires:
    - User is authenticated
    - User status is 'active'
    - User email is verified
    """

    message = "User account is not active or email is not verified."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user is active and verified."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Check user status
        if hasattr(request.user, "status"):
            if request.user.status != "active":
                return False

        # Check email verification
        if hasattr(request.user, "is_email_verified"):
            if not request.user.is_email_verified:
                return False

        return True


class IsPremiumUser(permissions.BasePermission):
    """Permission for premium users only.

    Requires:
    - User is authenticated
    - User role is 'premium' or 'superadmin'
    """

    message = "This feature requires a premium subscription."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user has premium role."""
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, "role"):
            return request.user.role in ("premium", "superadmin")

        return False


class IsSuperAdmin(permissions.BasePermission):
    """Permission for superadmin users only.

    Requires:
    - User is authenticated
    - User role is 'superadmin'
    """

    message = "This action requires superadmin privileges."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user is superadmin."""
        if not request.user or not request.user.is_authenticated:
            return False

        if hasattr(request.user, "role"):
            return request.user.role == "superadmin"

        return False


class IsOwner(permissions.BasePermission):
    """Permission that checks if user owns the object via tenant_id.

    For tenant-scoped objects, this ensures the object belongs to
    the authenticated user's tenant.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any
    ) -> bool:
        """Check if user owns the object."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get user's tenant_id
        user_tenant_id = getattr(request.user, "tenant_id", None)
        if not user_tenant_id:
            return False

        # Check object's tenant_id
        obj_tenant_id = getattr(obj, "tenant_id", None)
        if not obj_tenant_id:
            # Object doesn't have tenant_id, allow access
            return True

        return str(user_tenant_id) == str(obj_tenant_id)


class ReadOnly(permissions.BasePermission):
    """Permission that only allows read-only access.

    Allows GET, HEAD, and OPTIONS requests only.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if request is read-only."""
        return request.method in permissions.SAFE_METHODS


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission that allows read-only access to anyone, but write access only to owner.

    Combines ReadOnly and IsOwner permissions.
    """

    message = "You do not have permission to modify this resource."

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any
    ) -> bool:
        """Check permissions for object access."""
        # Read-only methods are allowed for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write methods require ownership
        if not request.user or not request.user.is_authenticated:
            return False

        user_tenant_id = getattr(request.user, "tenant_id", None)
        obj_tenant_id = getattr(obj, "tenant_id", None)

        if not user_tenant_id or not obj_tenant_id:
            return False

        return str(user_tenant_id) == str(obj_tenant_id)


class HasRole(permissions.BasePermission):
    """Dynamic permission that checks for specific roles.

    Usage:
        permission_classes = [HasRole]

        def get_permissions(self):
            if self.action == 'create':
                return [HasRole(['premium', 'superadmin'])]
            return super().get_permissions()
    """

    def __init__(self, allowed_roles: list[str] | None = None) -> None:
        """Initialize with allowed roles.

        Args:
            allowed_roles: List of role names that are allowed access.
        """
        self.allowed_roles = allowed_roles or []

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user has one of the allowed roles."""
        if not request.user or not request.user.is_authenticated:
            return False

        if not self.allowed_roles:
            return True

        user_role = getattr(request.user, "role", None)
        return user_role in self.allowed_roles


class CanCreateAccount(permissions.BasePermission):
    """Permission to check if user can create more accounts.

    Enforces account limits based on user role:
    - User: 3 accounts
    - Premium: Unlimited
    - SuperAdmin: Unlimited
    """

    message = "Account limit reached. Upgrade to premium for unlimited accounts."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user can create more accounts."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Only check on create action
        if getattr(view, "action", None) != "create":
            return True

        user_role = getattr(request.user, "role", "user")
        user_tenant_id = getattr(request.user, "tenant_id", None)

        # Premium and superadmin have no limits
        if user_role in ("premium", "superadmin"):
            return True

        # Count existing accounts
        from modules.finance.infrastructure.models import Account

        if not user_tenant_id:
            return False

        account_count = Account.objects.filter(tenant_id=user_tenant_id).count()
        limit = 3  # User role limit

        if account_count >= limit:
            return False

        return True


class TenantIsolation(permissions.BasePermission):
    """Permission that ensures tenant isolation.

    All objects must belong to the authenticated user's tenant.
    This is a safety net to prevent cross-tenant data access.
    """

    message = "Access denied: resource belongs to another tenant."

    def has_object_permission(
        self, request: Request, view: APIView, obj: Any
    ) -> bool:
        """Ensure object belongs to user's tenant."""
        if not request.user or not request.user.is_authenticated:
            return False

        user_tenant_id = getattr(request.user, "tenant_id", None)
        obj_tenant_id = getattr(obj, "tenant_id", None)

        # If object doesn't have tenant_id, skip this check
        if obj_tenant_id is None:
            return True

        # Superadmins can access all tenants (admin use only)
        if getattr(request.user, "role", None) == "superadmin":
            if getattr(request.user, "is_staff", False):
                return True

        if not user_tenant_id:
            return False

        return str(user_tenant_id) == str(obj_tenant_id)


# =============================================================================
# Subscription-Based Permission Classes
# =============================================================================


class HasFeature(permissions.BasePermission):
    """Permission that checks if subscription tier includes a feature.

    Usage:
        class MyViewSet(ViewSet):
            permission_classes = [IsAuthenticated, HasFeature]
            feature_code = "reports.advanced"

        Or dynamically:
            def get_permissions(self):
                if self.action == 'export_pdf':
                    return [IsAuthenticated(), HasFeature("export.pdf")]
                return super().get_permissions()
    """

    message = "This feature requires a premium subscription."

    def __init__(self, feature_code: str | None = None) -> None:
        """Initialize with optional feature code.

        Args:
            feature_code: The feature code to check. If not provided,
                         will look for `feature_code` attribute on the view.
        """
        self.feature_code = feature_code

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user's subscription includes the feature."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get feature code from init or view
        feature_code = self.feature_code or getattr(view, "feature_code", None)
        if not feature_code:
            # No feature code specified, allow access
            return True

        # Check subscription context
        from shared.middleware import get_subscription_context

        context = get_subscription_context()
        if context and context.has_feature(feature_code):
            return True

        # Fallback to service check
        from modules.subscriptions.domain.services import PermissionService

        return PermissionService.has_feature(request.user, feature_code)


class WithinUsageLimit(permissions.BasePermission):
    """Permission that checks if user is within their usage limit.

    Usage:
        class AccountViewSet(ViewSet):
            permission_classes = [IsAuthenticated, WithinUsageLimit]
            limit_key = "accounts_max"

        Or dynamically:
            def get_permissions(self):
                if self.action == 'create':
                    return [IsAuthenticated(), WithinUsageLimit("accounts_max")]
                return super().get_permissions()
    """

    message = "Usage limit exceeded. Upgrade to premium for unlimited access."

    def __init__(self, limit_key: str | None = None) -> None:
        """Initialize with optional limit key.

        Args:
            limit_key: The limit key to check. If not provided,
                      will look for `limit_key` attribute on the view.
        """
        self.limit_key = limit_key

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user is within their usage limit."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Only check on create action
        if getattr(view, "action", None) != "create":
            return True

        # Get limit key from init or view
        limit_key = self.limit_key or getattr(view, "limit_key", None)
        if not limit_key:
            # No limit key specified, allow access
            return True

        # Check usage limit
        from modules.subscriptions.domain.services import UsageLimitService

        allowed, error_message = UsageLimitService.can_perform_action(
            request.user, limit_key
        )
        if not allowed and error_message:
            self.message = error_message

        return allowed


class HasApiAccess(permissions.BasePermission):
    """Permission for API access (JWT-authenticated requests).

    Premium users only have API access. Web session requests are always allowed.

    Usage:
        permission_classes = [IsAuthenticated, HasApiAccess]
    """

    message = "API access requires a premium subscription. Use the web interface or upgrade."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user has API access."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Session-based requests (web UI) are always allowed
        if not hasattr(request, "auth") or not request.auth:
            return True

        # JWT-authenticated requests require API access feature
        from modules.subscriptions.domain.enums import FeatureCode
        from modules.subscriptions.domain.services import PermissionService

        return PermissionService.has_feature(
            request.user, FeatureCode.API_ACCESS.value
        )


class CanExport(permissions.BasePermission):
    """Permission that checks export format permissions.

    Free users can only export CSV. Premium users can export all formats.

    Usage:
        @action(detail=False, methods=["get"])
        def export(self, request):
            format = request.query_params.get("format", "csv")
            if not CanExport(format).has_permission(request, self):
                raise PermissionDenied("Export format requires premium")
    """

    message = "This export format requires a premium subscription."

    # Map export formats to feature codes
    FORMAT_FEATURES = {
        "csv": "export.csv",
        "json": "export.json",
        "pdf": "export.pdf",
    }

    def __init__(self, export_format: str = "csv") -> None:
        """Initialize with export format.

        Args:
            export_format: The export format (csv, json, pdf).
        """
        self.export_format = export_format.lower()

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user can export in the requested format."""
        if not request.user or not request.user.is_authenticated:
            return False

        # Get feature code for format
        feature_code = self.FORMAT_FEATURES.get(self.export_format)
        if not feature_code:
            # Unknown format, deny access
            return False

        # CSV is free for everyone
        if self.export_format == "csv":
            return True

        # Other formats require the feature
        from modules.subscriptions.domain.services import PermissionService

        return PermissionService.has_feature(request.user, feature_code)
