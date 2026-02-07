"""Django admin configuration for finance models."""

from django.contrib import admin
from django.db.models import Sum
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


class TenantScopedAdmin(admin.ModelAdmin):
    """Base admin class that filters by tenant for non-superadmins."""

    def get_queryset(self, request):
        """Filter queryset by tenant unless superadmin."""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # For non-superadmins, filter by their tenant
        return qs.filter(tenant_id=getattr(request.user, "tenant_id", None))


@admin.register(Category)
class CategoryAdmin(TenantScopedAdmin):
    """Admin configuration for Category."""

    list_display = ["name", "parent", "is_income", "is_system", "tenant_id"]
    list_filter = ["is_income", "is_system"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Account)
class AccountAdmin(TenantScopedAdmin):
    """Admin configuration for Account."""

    list_display = [
        "name",
        "account_type",
        "currency_code",
        "status",
        "institution",
        "is_included_in_net_worth",
        "display_order",
    ]
    list_filter = ["account_type", "status", "currency_code", "is_included_in_net_worth"]
    search_fields = ["name", "institution"]
    ordering = ["display_order", "name"]
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]

    fieldsets = [
        (None, {"fields": ["name", "account_type", "currency_code", "status"]}),
        ("Details", {"fields": ["institution", "account_number_masked", "notes"]}),
        ("Display", {"fields": ["is_included_in_net_worth", "display_order"]}),
        ("System", {"fields": ["id", "tenant_id", "created_at", "updated_at"]}),
    ]


@admin.register(Transaction)
class TransactionAdmin(TenantScopedAdmin):
    """Admin configuration for Transaction."""

    list_display = [
        "transaction_date",
        "account",
        "transaction_type_display",
        "amount_display",
        "status",
        "category",
        "description_short",
    ]
    list_filter = ["transaction_type", "status", "account", "category", "transaction_date"]
    search_fields = ["description", "reference_number", "notes"]
    date_hierarchy = "transaction_date"
    ordering = ["-transaction_date", "-created_at"]
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at", "posted_at"]
    raw_id_fields = ["account", "category", "adjustment_for"]

    fieldsets = [
        (None, {"fields": ["account", "transaction_type", "amount", "currency_code"]}),
        ("Timing", {"fields": ["transaction_date", "status", "posted_at"]}),
        ("Details", {"fields": ["description", "category", "reference_number", "notes"]}),
        ("Advanced", {"fields": ["idempotency_key", "adjustment_for", "exchange_rate"]}),
        ("System", {"fields": ["id", "tenant_id", "created_at", "updated_at"]}),
    ]

    @admin.display(description="Type")
    def transaction_type_display(self, obj):
        """Display transaction type with color."""
        if obj.transaction_type == Transaction.TransactionType.CREDIT:
            return format_html('<span style="color: green;">Credit</span>')
        return format_html('<span style="color: red;">Debit</span>')

    @admin.display(description="Amount")
    def amount_display(self, obj):
        """Display amount with sign and color."""
        if obj.transaction_type == Transaction.TransactionType.CREDIT:
            return format_html(
                '<span style="color: green;">+{} {}</span>',
                obj.amount,
                obj.currency_code,
            )
        return format_html(
            '<span style="color: red;">-{} {}</span>',
            obj.amount,
            obj.currency_code,
        )

    @admin.display(description="Description")
    def description_short(self, obj):
        """Truncate description for display."""
        if obj.description and len(obj.description) > 50:
            return f"{obj.description[:50]}..."
        return obj.description or "-"


@admin.register(Transfer)
class TransferAdmin(TenantScopedAdmin):
    """Admin configuration for Transfer."""

    list_display = [
        "transfer_date",
        "from_account",
        "to_account",
        "amount",
        "currency_code",
    ]
    list_filter = ["transfer_date", "from_account", "to_account"]
    date_hierarchy = "transfer_date"
    ordering = ["-transfer_date", "-created_at"]
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]
    raw_id_fields = ["from_account", "to_account", "from_transaction", "to_transaction"]


@admin.register(Asset)
class AssetAdmin(TenantScopedAdmin):
    """Admin configuration for Asset."""

    list_display = [
        "name",
        "asset_type",
        "current_value_display",
        "purchase_price",
        "gain_loss_display",
        "is_included_in_net_worth",
    ]
    list_filter = ["asset_type", "is_included_in_net_worth", "currency_code"]
    search_fields = ["name", "description"]
    ordering = ["name"]
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]

    @admin.display(description="Current Value")
    def current_value_display(self, obj):
        """Display current value with currency."""
        return f"{obj.current_value} {obj.currency_code}"

    @admin.display(description="Gain/Loss")
    def gain_loss_display(self, obj):
        """Display gain/loss if purchase price is known."""
        if obj.purchase_price is None:
            return "-"
        diff = obj.current_value - obj.purchase_price
        if diff > 0:
            return format_html('<span style="color: green;">+{}</span>', diff)
        elif diff < 0:
            return format_html('<span style="color: red;">{}</span>', diff)
        return "0"


@admin.register(Liability)
class LiabilityAdmin(TenantScopedAdmin):
    """Admin configuration for Liability."""

    list_display = [
        "name",
        "liability_type",
        "current_balance_display",
        "interest_rate",
        "minimum_payment",
        "due_day",
        "creditor",
    ]
    list_filter = ["liability_type", "is_included_in_net_worth", "currency_code"]
    search_fields = ["name", "creditor"]
    ordering = ["name"]
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]

    @admin.display(description="Balance")
    def current_balance_display(self, obj):
        """Display current balance with currency."""
        return format_html(
            '<span style="color: red;">{} {}</span>',
            obj.current_balance,
            obj.currency_code,
        )


@admin.register(Loan)
class LoanAdmin(TenantScopedAdmin):
    """Admin configuration for Loan."""

    list_display = [
        "name",
        "liability_type",
        "balance_display",
        "interest_rate",
        "payment_amount",
        "payment_frequency",
        "status",
        "progress_display",
    ]
    list_filter = ["liability_type", "status", "payment_frequency", "currency_code"]
    search_fields = ["name", "lender"]
    ordering = ["name"]
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]
    raw_id_fields = ["linked_account"]

    @admin.display(description="Balance")
    def balance_display(self, obj):
        """Display balance out of original principal."""
        return f"{obj.current_balance}/{obj.original_principal} {obj.currency_code}"

    @admin.display(description="Progress")
    def progress_display(self, obj):
        """Display payment progress as percentage."""
        if obj.original_principal == 0:
            return "100%"
        paid = obj.original_principal - obj.current_balance
        pct = (paid / obj.original_principal) * 100
        return f"{pct:.1f}%"


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    """Admin configuration for IdempotencyKey."""

    list_display = ["key", "resource_type", "resource_id", "tenant_id", "created_at", "expires_at"]
    list_filter = ["resource_type", "created_at"]
    search_fields = ["key", "resource_id"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at"]


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    """Admin configuration for ExchangeRate."""

    list_display = ["from_currency", "to_currency", "rate", "effective_date", "source"]
    list_filter = ["from_currency", "to_currency", "effective_date"]
    date_hierarchy = "effective_date"
    ordering = ["-effective_date", "from_currency", "to_currency"]
    readonly_fields = ["id", "created_at"]
