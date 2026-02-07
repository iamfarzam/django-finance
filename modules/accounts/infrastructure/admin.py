"""Django admin configuration for accounts module."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from modules.accounts.infrastructure.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshTokenBlacklist,
    User,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""

    list_display = (
        "email",
        "full_name",
        "role",
        "status_badge",
        "is_email_verified",
        "is_locked_display",
        "created_at",
    )
    list_filter = ("role", "status", "is_email_verified", "is_staff", "created_at")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "tenant_id",
        "created_at",
        "updated_at",
        "last_login_at",
        "failed_login_attempts",
        "locked_until",
    )

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {"fields": ("first_name", "last_name")},
        ),
        (
            "Status",
            {"fields": ("role", "status", "is_email_verified")},
        ),
        (
            "Security",
            {
                "fields": (
                    "failed_login_attempts",
                    "locked_until",
                    "last_login_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Tenant",
            {
                "fields": ("tenant_id",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "role",
                ),
            },
        ),
    )

    def status_badge(self, obj: User) -> str:
        """Display status with color badge."""
        colors = {
            "pending": "orange",
            "active": "green",
            "suspended": "red",
            "deleted": "gray",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def is_locked_display(self, obj: User) -> str:
        """Display lock status."""
        if obj.is_locked:
            return format_html(
                '<span style="color: red;">Locked until {}</span>',
                obj.locked_until.strftime("%Y-%m-%d %H:%M"),
            )
        return format_html('<span style="color: green;">Not locked</span>')

    is_locked_display.short_description = "Lock Status"

    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only see their own tenant
        return qs.filter(tenant_id=request.user.tenant_id)


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin for email verification tokens."""

    list_display = ("user", "email", "expires_at", "is_valid", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "email", "token")
    readonly_fields = ("token", "created_at")
    raw_id_fields = ("user",)

    def is_valid(self, obj: EmailVerificationToken) -> bool:
        return obj.is_valid

    is_valid.boolean = True


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for password reset tokens."""

    list_display = ("user", "expires_at", "is_valid", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "token")
    readonly_fields = ("token", "created_at")
    raw_id_fields = ("user",)

    def is_valid(self, obj: PasswordResetToken) -> bool:
        return obj.is_valid

    is_valid.boolean = True


@admin.register(RefreshTokenBlacklist)
class RefreshTokenBlacklistAdmin(admin.ModelAdmin):
    """Admin for blacklisted refresh tokens."""

    list_display = ("token_jti", "user", "blacklisted_at", "expires_at")
    list_filter = ("blacklisted_at",)
    search_fields = ("user__email", "token_jti")
    readonly_fields = ("token_jti", "blacklisted_at")
    raw_id_fields = ("user",)

    actions = ["cleanup_expired"]

    @admin.action(description="Clean up expired tokens")
    def cleanup_expired(self, request, queryset):
        deleted = RefreshTokenBlacklist.cleanup_expired()
        self.message_user(request, f"Removed {deleted} expired tokens.")
