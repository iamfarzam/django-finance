"""Base admin classes and mixins for Django Finance platform.

This module provides reusable admin components:
- TenantScopedAdmin: Base class that filters by tenant
- AuditLogMixin: Mixin for logging admin actions
- ExportMixin: Mixin for exporting data
- ReadOnlyAdminMixin: Mixin for read-only admin views
"""

import csv
from io import StringIO
from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from shared.audit import AuditAction, AuditCategory, audit_logger


class TenantScopedAdmin(admin.ModelAdmin):
    """Base admin class that filters queryset by tenant.

    Non-superadmin users will only see records belonging to their tenant.
    Superadmins can see all records across tenants.
    """

    def get_queryset(self, request: HttpRequest):
        """Filter queryset by tenant unless superadmin."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # For non-superadmins, filter by their tenant
        tenant_id = getattr(request.user, "tenant_id", None)
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs.none()

    def save_model(self, request: HttpRequest, obj: Any, form: Any, change: bool):
        """Set tenant_id on create if not already set."""
        if not change and hasattr(obj, "tenant_id") and not obj.tenant_id:
            obj.tenant_id = getattr(request.user, "tenant_id", None)
        super().save_model(request, obj, form, change)


class AuditLogMixin:
    """Mixin that logs admin actions to the audit log.

    Automatically logs:
    - Object creation
    - Object updates (with before/after values)
    - Object deletion
    """

    def save_model(self, request: HttpRequest, obj: Any, form: Any, change: bool):
        """Log create/update actions."""
        if change:
            # Get old values before save
            old_obj = self.model.objects.filter(pk=obj.pk).first()
            old_data = {field.name: getattr(old_obj, field.name) for field in obj._meta.fields}
        else:
            old_data = None

        super().save_model(request, obj, form, change)

        # Log the action
        action = AuditAction.ADMIN_DATA_EXPORT if change else AuditAction.ACCOUNT_CREATE
        resource_type = obj._meta.model_name

        if change and old_data:
            new_data = {field.name: getattr(obj, field.name) for field in obj._meta.fields}
            audit_logger.log_update(
                action=action,
                tenant_id=getattr(request.user, "tenant_id", None),
                user_id=str(request.user.pk),
                resource_type=resource_type,
                resource_id=str(obj.pk),
                old_data=old_data,
                new_data=new_data,
                request=request,
            )
        else:
            audit_logger.log_create(
                action=action,
                tenant_id=getattr(request.user, "tenant_id", None),
                user_id=str(request.user.pk),
                resource_type=resource_type,
                resource_id=str(obj.pk),
                created_data={field.name: str(getattr(obj, field.name)) for field in obj._meta.fields},
                request=request,
            )

    def delete_model(self, request: HttpRequest, obj: Any):
        """Log delete actions."""
        resource_type = obj._meta.model_name
        obj_pk = str(obj.pk)
        deleted_data = {field.name: str(getattr(obj, field.name)) for field in obj._meta.fields}

        super().delete_model(request, obj)

        audit_logger.log_delete(
            action=AuditAction.ADMIN_DATA_DELETE,
            tenant_id=getattr(request.user, "tenant_id", None),
            user_id=str(request.user.pk),
            resource_type=resource_type,
            resource_id=obj_pk,
            deleted_data=deleted_data,
            request=request,
        )


class ExportMixin:
    """Mixin that adds CSV export action to admin."""

    actions = ["export_as_csv"]

    @admin.action(description="Export selected items as CSV")
    def export_as_csv(self, request: HttpRequest, queryset):
        """Export selected items as CSV file."""
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(field_names)

        for obj in queryset:
            row = [str(getattr(obj, field)) for field in field_names]
            writer.writerow(row)

        # Create response
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta.model_name}_export.csv"

        # Log the export
        audit_logger.log_action(
            action=AuditAction.ADMIN_DATA_EXPORT,
            tenant_id=getattr(request.user, "tenant_id", None),
            user_id=str(request.user.pk),
            resource_type=meta.model_name,
            request=request,
            details={
                "export_count": queryset.count(),
                "export_format": "csv",
            },
            category=AuditCategory.ADMIN,
        )

        return response


class ReadOnlyAdminMixin:
    """Mixin that makes admin view read-only.

    Useful for sensitive data that should only be viewed, not modified.
    """

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable add permission."""
        return False

    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable change permission."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable delete permission."""
        return False


class SoftDeleteMixin:
    """Mixin for models with soft delete (status field).

    Adds actions for soft delete and restore.
    """

    actions = ["soft_delete", "restore"]

    @admin.action(description="Soft delete selected items")
    def soft_delete(self, request: HttpRequest, queryset):
        """Mark items as deleted without removing from database."""
        count = queryset.update(status="deleted", updated_at=timezone.now())
        self.message_user(request, f"Soft deleted {count} items.")

    @admin.action(description="Restore selected items")
    def restore(self, request: HttpRequest, queryset):
        """Restore soft-deleted items."""
        count = queryset.filter(status="deleted").update(status="active", updated_at=timezone.now())
        self.message_user(request, f"Restored {count} items.")
