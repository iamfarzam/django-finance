"""Django admin configuration for finance models.

Enhanced admin with:
- Tenant-scoped filtering
- Bulk actions for common workflows
- Inline editing for related models
- Export capabilities
- Custom list displays and filters
"""

from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html

from modules.finance.infrastructure.models import (
    Account,
    Asset,
    Category,
    ExchangeRate,
    IdempotencyKey,
    Liability,
    Loan,
    Transaction,
    Transfer,
)
from shared.admin.base import AuditLogMixin, ExportMixin, TenantScopedAdmin


# =============================================================================
# Inline Admin Classes
# =============================================================================


class TransactionInline(admin.TabularInline):
    """Inline for viewing recent transactions on an account."""

    model = Transaction
    extra = 0
    max_num = 10
    readonly_fields = [
        "transaction_date",
        "transaction_type",
        "amount",
        "currency_code",
        "description",
        "status",
    ]
    fields = readonly_fields
    can_delete = False
    show_change_link = True

    def get_queryset(self, request):
        """Limit to recent transactions."""
        qs = super().get_queryset(request)
        return qs.order_by("-transaction_date")[:10]

    def has_add_permission(self, request, obj=None):
        return False


# =============================================================================
# Model Admin Classes
# =============================================================================


@admin.register(Category)
class CategoryAdmin(TenantScopedAdmin, ExportMixin):
    """Admin configuration for Category."""

    list_display = ["name", "parent", "is_income", "is_system", "icon", "tenant_id"]
    list_filter = ["is_income", "is_system", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["name"]
    list_editable = ["is_income", "is_system"]
    list_per_page = 50
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]

    fieldsets = [
        (None, {"fields": ["name", "parent", "description"]}),
        ("Settings", {"fields": ["is_income", "is_system", "icon", "color"]}),
        (
            "System",
            {
                "fields": ["id", "tenant_id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["mark_as_income", "mark_as_expense", "export_as_csv"]

    @admin.action(description="Mark selected categories as income")
    def mark_as_income(self, request, queryset):
        count = queryset.update(is_income=True)
        self.message_user(request, f"Marked {count} categories as income.")

    @admin.action(description="Mark selected categories as expense")
    def mark_as_expense(self, request, queryset):
        count = queryset.update(is_income=False)
        self.message_user(request, f"Marked {count} categories as expense.")


@admin.register(Account)
class AccountAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin configuration for Account with enhanced features."""

    list_display = [
        "name",
        "account_type",
        "currency_code",
        "status_badge",
        "institution",
        "is_included_in_net_worth",
        "display_order",
        "created_at",
    ]
    list_filter = [
        "account_type",
        "status",
        "currency_code",
        "is_included_in_net_worth",
        "created_at",
    ]
    search_fields = ["name", "institution", "notes"]
    ordering = ["display_order", "name"]
    list_editable = ["display_order", "is_included_in_net_worth"]
    list_per_page = 25
    date_hierarchy = "created_at"
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]
    inlines = [TransactionInline]

    fieldsets = [
        (None, {"fields": ["name", "account_type", "currency_code", "status"]}),
        (
            "Details",
            {"fields": ["institution", "account_number_masked", "notes"]},
        ),
        (
            "Display",
            {"fields": ["is_included_in_net_worth", "display_order"]},
        ),
        (
            "System",
            {
                "fields": ["id", "tenant_id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = [
        "activate_accounts",
        "close_accounts",
        "include_in_net_worth",
        "exclude_from_net_worth",
        "export_as_csv",
    ]

    @admin.display(description="Status")
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            "active": "#10b981",
            "inactive": "#6b7280",
            "closed": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description="Activate selected accounts")
    def activate_accounts(self, request, queryset):
        count = queryset.update(status="active", updated_at=timezone.now())
        self.message_user(request, f"Activated {count} accounts.", messages.SUCCESS)

    @admin.action(description="Close selected accounts")
    def close_accounts(self, request, queryset):
        count = queryset.update(status="closed", updated_at=timezone.now())
        self.message_user(request, f"Closed {count} accounts.", messages.WARNING)

    @admin.action(description="Include in net worth calculation")
    def include_in_net_worth(self, request, queryset):
        count = queryset.update(is_included_in_net_worth=True)
        self.message_user(request, f"Included {count} accounts in net worth.")

    @admin.action(description="Exclude from net worth calculation")
    def exclude_from_net_worth(self, request, queryset):
        count = queryset.update(is_included_in_net_worth=False)
        self.message_user(request, f"Excluded {count} accounts from net worth.")


@admin.register(Transaction)
class TransactionAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin configuration for Transaction with enhanced features."""

    list_display = [
        "transaction_date",
        "account_link",
        "transaction_type_badge",
        "amount_display",
        "status_badge",
        "category",
        "description_short",
    ]
    list_filter = [
        "transaction_type",
        "status",
        "account",
        "category",
        ("transaction_date", admin.DateFieldListFilter),
    ]
    search_fields = ["description", "reference_number", "notes"]
    date_hierarchy = "transaction_date"
    ordering = ["-transaction_date", "-created_at"]
    list_per_page = 50
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at", "posted_at"]
    raw_id_fields = ["account", "category", "adjustment_for"]
    autocomplete_fields = ["account", "category"]

    fieldsets = [
        (
            None,
            {"fields": ["account", "transaction_type", "amount", "currency_code"]},
        ),
        ("Timing", {"fields": ["transaction_date", "status", "posted_at"]}),
        (
            "Details",
            {"fields": ["description", "category", "reference_number", "notes"]},
        ),
        (
            "Advanced",
            {
                "fields": ["idempotency_key", "adjustment_for", "exchange_rate"],
                "classes": ["collapse"],
            },
        ),
        (
            "System",
            {
                "fields": ["id", "tenant_id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = [
        "post_transactions",
        "void_transactions",
        "mark_pending",
        "export_as_csv",
    ]

    @admin.display(description="Account")
    def account_link(self, obj):
        """Display account as a link."""
        return format_html(
            '<a href="/admin/finance/account/{}/change/">{}</a>',
            obj.account_id,
            obj.account.name,
        )

    @admin.display(description="Type")
    def transaction_type_badge(self, obj):
        """Display transaction type with color badge."""
        if obj.transaction_type == Transaction.TransactionType.CREDIT:
            return format_html(
                '<span style="color: #10b981; font-weight: 600;">&#9650; Credit</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: 600;">&#9660; Debit</span>'
        )

    @admin.display(description="Amount")
    def amount_display(self, obj):
        """Display amount with sign and color."""
        if obj.transaction_type == Transaction.TransactionType.CREDIT:
            return format_html(
                '<span style="color: #10b981; font-weight: 600;">+{} {}</span>',
                obj.amount,
                obj.currency_code,
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: 600;">-{} {}</span>',
            obj.amount,
            obj.currency_code,
        )

    @admin.display(description="Status")
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            "pending": "#f59e0b",
            "posted": "#10b981",
            "voided": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Description")
    def description_short(self, obj):
        """Truncate description for display."""
        if obj.description and len(obj.description) > 40:
            return f"{obj.description[:40]}..."
        return obj.description or "-"

    @admin.action(description="Post selected transactions")
    def post_transactions(self, request, queryset):
        count = queryset.filter(status="pending").update(
            status="posted", posted_at=timezone.now(), updated_at=timezone.now()
        )
        self.message_user(request, f"Posted {count} transactions.", messages.SUCCESS)

    @admin.action(description="Void selected transactions")
    def void_transactions(self, request, queryset):
        count = queryset.exclude(status="voided").update(
            status="voided", updated_at=timezone.now()
        )
        self.message_user(request, f"Voided {count} transactions.", messages.WARNING)

    @admin.action(description="Mark as pending")
    def mark_pending(self, request, queryset):
        count = queryset.update(status="pending", updated_at=timezone.now())
        self.message_user(request, f"Marked {count} transactions as pending.")


@admin.register(Transfer)
class TransferAdmin(TenantScopedAdmin, ExportMixin):
    """Admin configuration for Transfer."""

    list_display = [
        "transfer_date",
        "from_account",
        "transfer_arrow",
        "to_account",
        "amount_display",
    ]
    list_filter = ["transfer_date", "from_account", "to_account", "currency_code"]
    date_hierarchy = "transfer_date"
    ordering = ["-transfer_date", "-created_at"]
    list_per_page = 25
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]
    raw_id_fields = ["from_account", "to_account", "from_transaction", "to_transaction"]

    fieldsets = [
        (None, {"fields": ["from_account", "to_account"]}),
        ("Amount", {"fields": ["amount", "currency_code", "transfer_date"]}),
        (
            "Linked Transactions",
            {
                "fields": ["from_transaction", "to_transaction"],
                "classes": ["collapse"],
            },
        ),
        (
            "System",
            {
                "fields": ["id", "tenant_id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="")
    def transfer_arrow(self, obj):
        return format_html('<span style="font-size: 18px;">&#8594;</span>')

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight: 600;">{} {}</span>',
            obj.amount,
            obj.currency_code,
        )


@admin.register(Asset)
class AssetAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin configuration for Asset."""

    list_display = [
        "name",
        "asset_type",
        "current_value_display",
        "purchase_price_display",
        "gain_loss_display",
        "is_included_in_net_worth",
    ]
    list_filter = ["asset_type", "is_included_in_net_worth", "currency_code", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["name"]
    list_per_page = 25
    list_editable = ["is_included_in_net_worth"]
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]

    fieldsets = [
        (None, {"fields": ["name", "asset_type", "description"]}),
        (
            "Valuation",
            {"fields": ["current_value", "purchase_price", "purchase_date", "currency_code"]},
        ),
        ("Settings", {"fields": ["is_included_in_net_worth"]}),
        (
            "System",
            {
                "fields": ["id", "tenant_id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["include_in_net_worth", "exclude_from_net_worth", "export_as_csv"]

    @admin.display(description="Current Value")
    def current_value_display(self, obj):
        return format_html(
            '<span style="font-weight: 600;">{} {}</span>',
            obj.current_value,
            obj.currency_code,
        )

    @admin.display(description="Purchase Price")
    def purchase_price_display(self, obj):
        if obj.purchase_price:
            return f"{obj.purchase_price} {obj.currency_code}"
        return "-"

    @admin.display(description="Gain/Loss")
    def gain_loss_display(self, obj):
        if obj.purchase_price is None:
            return "-"
        diff = obj.current_value - obj.purchase_price
        if diff > 0:
            return format_html('<span style="color: #10b981; font-weight: 600;">+{}</span>', diff)
        elif diff < 0:
            return format_html('<span style="color: #ef4444; font-weight: 600;">{}</span>', diff)
        return format_html('<span style="color: #6b7280;">0</span>')

    @admin.action(description="Include in net worth")
    def include_in_net_worth(self, request, queryset):
        count = queryset.update(is_included_in_net_worth=True)
        self.message_user(request, f"Included {count} assets in net worth.")

    @admin.action(description="Exclude from net worth")
    def exclude_from_net_worth(self, request, queryset):
        count = queryset.update(is_included_in_net_worth=False)
        self.message_user(request, f"Excluded {count} assets from net worth.")


@admin.register(Liability)
class LiabilityAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin configuration for Liability."""

    list_display = [
        "name",
        "liability_type",
        "current_balance_display",
        "interest_rate_display",
        "minimum_payment",
        "due_day",
        "creditor",
    ]
    list_filter = ["liability_type", "is_included_in_net_worth", "currency_code"]
    search_fields = ["name", "creditor"]
    ordering = ["name"]
    list_per_page = 25
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]

    fieldsets = [
        (None, {"fields": ["name", "liability_type", "creditor"]}),
        (
            "Balance",
            {"fields": ["current_balance", "currency_code", "interest_rate"]},
        ),
        (
            "Payment",
            {"fields": ["minimum_payment", "due_day"]},
        ),
        ("Settings", {"fields": ["is_included_in_net_worth"]}),
        (
            "System",
            {
                "fields": ["id", "tenant_id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Balance")
    def current_balance_display(self, obj):
        return format_html(
            '<span style="color: #ef4444; font-weight: 600;">{} {}</span>',
            obj.current_balance,
            obj.currency_code,
        )

    @admin.display(description="Interest Rate")
    def interest_rate_display(self, obj):
        if obj.interest_rate:
            return f"{obj.interest_rate}%"
        return "-"


@admin.register(Loan)
class LoanAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin configuration for Loan."""

    list_display = [
        "name",
        "liability_type",
        "balance_display",
        "interest_rate_display",
        "payment_display",
        "status_badge",
        "progress_bar",
    ]
    list_filter = ["liability_type", "status", "payment_frequency", "currency_code"]
    search_fields = ["name", "lender"]
    ordering = ["name"]
    list_per_page = 25
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]
    raw_id_fields = ["linked_account"]

    fieldsets = [
        (None, {"fields": ["name", "liability_type", "lender"]}),
        (
            "Loan Details",
            {"fields": ["original_principal", "current_balance", "currency_code", "interest_rate"]},
        ),
        (
            "Payment Schedule",
            {"fields": ["payment_amount", "payment_frequency", "next_payment_date"]},
        ),
        ("Status", {"fields": ["status", "start_date", "end_date"]}),
        (
            "Linked Account",
            {
                "fields": ["linked_account"],
                "classes": ["collapse"],
            },
        ),
        (
            "System",
            {
                "fields": ["id", "tenant_id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["mark_active", "mark_paid_off", "export_as_csv"]

    @admin.display(description="Balance")
    def balance_display(self, obj):
        return format_html(
            '<span style="color: #ef4444;">{}</span> / {} {}',
            obj.current_balance,
            obj.original_principal,
            obj.currency_code,
        )

    @admin.display(description="Interest")
    def interest_rate_display(self, obj):
        if obj.interest_rate:
            return f"{obj.interest_rate}%"
        return "-"

    @admin.display(description="Payment")
    def payment_display(self, obj):
        if obj.payment_amount:
            return f"{obj.payment_amount} / {obj.get_payment_frequency_display()}"
        return "-"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "active": "#10b981",
            "paid_off": "#3b82f6",
            "defaulted": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Progress")
    def progress_bar(self, obj):
        if obj.original_principal == 0:
            pct = 100
        else:
            paid = obj.original_principal - obj.current_balance
            pct = (paid / obj.original_principal) * 100

        color = "#10b981" if pct >= 75 else "#f59e0b" if pct >= 50 else "#ef4444"
        return format_html(
            '<div style="width: 100px; height: 8px; background: #e5e7eb; border-radius: 4px;">'
            '<div style="width: {}%; height: 100%; background: {}; border-radius: 4px;"></div>'
            '</div><span style="font-size: 10px; color: #6b7280;">{:.1f}%</span>',
            min(pct, 100),
            color,
            pct,
        )

    @admin.action(description="Mark as active")
    def mark_active(self, request, queryset):
        count = queryset.update(status="active")
        self.message_user(request, f"Marked {count} loans as active.")

    @admin.action(description="Mark as paid off")
    def mark_paid_off(self, request, queryset):
        count = queryset.update(status="paid_off", current_balance=Decimal("0.00"))
        self.message_user(request, f"Marked {count} loans as paid off.")


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    """Admin configuration for IdempotencyKey."""

    list_display = ["key", "resource_type", "resource_id", "tenant_id", "created_at", "expires_at", "is_expired"]
    list_filter = ["resource_type", "created_at"]
    search_fields = ["key", "resource_id"]
    ordering = ["-created_at"]
    list_per_page = 50
    readonly_fields = ["id", "created_at"]

    actions = ["cleanup_expired"]

    @admin.display(description="Expired", boolean=True)
    def is_expired(self, obj):
        return obj.expires_at < timezone.now()

    @admin.action(description="Clean up expired keys")
    def cleanup_expired(self, request, queryset):
        count = queryset.filter(expires_at__lt=timezone.now()).delete()[0]
        self.message_user(request, f"Deleted {count} expired idempotency keys.")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Admin configuration for ExchangeRate."""

    list_display = ["from_currency", "to_currency", "rate", "effective_date", "source"]
    list_filter = ["from_currency", "to_currency", "effective_date", "source"]
    date_hierarchy = "effective_date"
    ordering = ["-effective_date", "from_currency", "to_currency"]
    list_per_page = 50
    readonly_fields = ["id", "created_at"]

    fieldsets = [
        (None, {"fields": ["from_currency", "to_currency", "rate"]}),
        ("Details", {"fields": ["effective_date", "source"]}),
        (
            "System",
            {
                "fields": ["id", "created_at"],
                "classes": ["collapse"],
            },
        ),
    ]
