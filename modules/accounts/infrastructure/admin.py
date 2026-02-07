"""Django admin configuration for accounts module.

Enhanced admin with:
- Custom branding and displays
- User management workflows
- Token management and cleanup
- Security monitoring displays
- Export capabilities
"""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.utils.html import format_html

from modules.accounts.infrastructure.models import (
    EmailVerificationToken,
    PasswordResetToken,
    RefreshTokenBlacklist,
    User,
)
from shared.admin.base import ExportMixin


@admin.register(User)
class UserAdmin(BaseUserAdmin, ExportMixin):
    """Admin configuration for User model with enhanced features."""

    list_display = (
        "email",
        "full_name",
        "role_badge",
        "status_badge",
        "is_email_verified_badge",
        "is_locked_display",
        "last_login_display",
        "created_at",
    )
    list_filter = ("role", "status", "is_email_verified", "is_staff", "is_superuser", "created_at")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-created_at",)
    list_per_page = 25
    date_hierarchy = "created_at"
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

    actions = [
        "activate_users",
        "suspend_users",
        "verify_emails",
        "unlock_accounts",
        "make_premium",
        "revoke_premium",
        "export_as_csv",
    ]

    @admin.display(description="Role")
    def role_badge(self, obj: User) -> str:
        """Display role with color badge."""
        colors = {
            "user": "#6b7280",
            "premium": "#8b5cf6",
            "superadmin": "#ef4444",
        }
        color = colors.get(obj.role, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_role_display(),
        )

    @admin.display(description="Status")
    def status_badge(self, obj: User) -> str:
        """Display status with color badge."""
        colors = {
            "pending": "#f59e0b",
            "active": "#10b981",
            "suspended": "#ef4444",
            "deleted": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Email Verified", boolean=True)
    def is_email_verified_badge(self, obj: User) -> bool:
        """Display email verification status as boolean."""
        return obj.is_email_verified

    @admin.display(description="Lock Status")
    def is_locked_display(self, obj: User) -> str:
        """Display lock status."""
        if obj.is_locked:
            return format_html(
                '<span style="color: #ef4444; font-weight: 500;">&#128274; Locked until {}</span>',
                obj.locked_until.strftime("%Y-%m-%d %H:%M"),
            )
        return format_html('<span style="color: #10b981;">&#128275; Unlocked</span>')

    @admin.display(description="Last Login")
    def last_login_display(self, obj: User) -> str:
        """Display last login time."""
        if obj.last_login_at:
            return obj.last_login_at.strftime("%Y-%m-%d %H:%M")
        return format_html('<span style="color: #6b7280;">Never</span>')

    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Non-superusers can only see their own tenant
        return qs.filter(tenant_id=request.user.tenant_id)

    @admin.action(description="Activate selected users")
    def activate_users(self, request, queryset):
        count = queryset.update(status="active", updated_at=timezone.now())
        self.message_user(request, f"Activated {count} users.", messages.SUCCESS)

    @admin.action(description="Suspend selected users")
    def suspend_users(self, request, queryset):
        count = queryset.exclude(is_superuser=True).update(status="suspended", updated_at=timezone.now())
        self.message_user(request, f"Suspended {count} users.", messages.WARNING)

    @admin.action(description="Mark emails as verified")
    def verify_emails(self, request, queryset):
        count = queryset.update(is_email_verified=True, updated_at=timezone.now())
        self.message_user(request, f"Verified {count} email addresses.")

    @admin.action(description="Unlock accounts")
    def unlock_accounts(self, request, queryset):
        count = queryset.update(
            locked_until=None,
            failed_login_attempts=0,
            updated_at=timezone.now(),
        )
        self.message_user(request, f"Unlocked {count} accounts.", messages.SUCCESS)

    @admin.action(description="Upgrade to Premium")
    def make_premium(self, request, queryset):
        count = queryset.filter(role="user").update(role="premium", updated_at=timezone.now())
        self.message_user(request, f"Upgraded {count} users to Premium.", messages.SUCCESS)

    @admin.action(description="Revoke Premium status")
    def revoke_premium(self, request, queryset):
        count = queryset.filter(role="premium").update(role="user", updated_at=timezone.now())
        self.message_user(request, f"Revoked Premium from {count} users.")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    """Admin for email verification tokens."""

    list_display = ("user_email", "email", "expires_at", "is_valid_badge", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "email", "token")
    ordering = ("-created_at",)
    list_per_page = 50
    readonly_fields = ("token", "created_at")
    raw_id_fields = ("user",)

    actions = ["cleanup_expired"]

    @admin.display(description="User")
    def user_email(self, obj: EmailVerificationToken) -> str:
        return obj.user.email

    @admin.display(description="Valid", boolean=True)
    def is_valid_badge(self, obj: EmailVerificationToken) -> bool:
        return obj.is_valid

    @admin.action(description="Clean up expired tokens")
    def cleanup_expired(self, request, queryset):
        count = queryset.filter(expires_at__lt=timezone.now()).delete()[0]
        self.message_user(request, f"Deleted {count} expired tokens.")


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin for password reset tokens."""

    list_display = ("user_email", "expires_at", "is_valid_badge", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "token")
    ordering = ("-created_at",)
    list_per_page = 50
    readonly_fields = ("token", "created_at")
    raw_id_fields = ("user",)

    actions = ["cleanup_expired"]

    @admin.display(description="User")
    def user_email(self, obj: PasswordResetToken) -> str:
        return obj.user.email

    @admin.display(description="Valid", boolean=True)
    def is_valid_badge(self, obj: PasswordResetToken) -> bool:
        return obj.is_valid

    @admin.action(description="Clean up expired tokens")
    def cleanup_expired(self, request, queryset):
        count = queryset.filter(expires_at__lt=timezone.now()).delete()[0]
        self.message_user(request, f"Deleted {count} expired tokens.")


@admin.register(RefreshTokenBlacklist)
class RefreshTokenBlacklistAdmin(admin.ModelAdmin):
    """Admin for blacklisted refresh tokens."""

    list_display = ("token_jti_short", "user_email", "blacklisted_at", "expires_at", "is_expired_badge")
    list_filter = ("blacklisted_at",)
    search_fields = ("user__email", "token_jti")
    ordering = ("-blacklisted_at",)
    list_per_page = 50
    readonly_fields = ("token_jti", "blacklisted_at")
    raw_id_fields = ("user",)

    actions = ["cleanup_expired"]

    @admin.display(description="Token JTI")
    def token_jti_short(self, obj: RefreshTokenBlacklist) -> str:
        return obj.token_jti[:16] + "..."

    @admin.display(description="User")
    def user_email(self, obj: RefreshTokenBlacklist) -> str:
        return obj.user.email

    @admin.display(description="Expired", boolean=True)
    def is_expired_badge(self, obj: RefreshTokenBlacklist) -> bool:
        return obj.expires_at < timezone.now()

    @admin.action(description="Clean up expired tokens")
    def cleanup_expired(self, request, queryset):
        deleted = RefreshTokenBlacklist.cleanup_expired()
        self.message_user(request, f"Removed {deleted} expired tokens.")
