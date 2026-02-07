"""Shared admin components for Django Finance platform.

This package provides:
- Custom admin site with branding
- Base admin classes with tenant scoping
- Common admin mixins and utilities
- Audit log visibility
"""

from shared.admin.base import (
    AuditLogMixin,
    ExportMixin,
    ReadOnlyAdminMixin,
    TenantScopedAdmin,
)
from shared.admin.site import finance_admin_site

__all__ = [
    "finance_admin_site",
    "TenantScopedAdmin",
    "AuditLogMixin",
    "ExportMixin",
    "ReadOnlyAdminMixin",
]
