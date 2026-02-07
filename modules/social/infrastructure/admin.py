"""Django admin configuration for the social finance module."""

from django.contrib import admin

from modules.social.infrastructure.models import (
    Contact,
    ContactGroup,
    ExpenseGroup,
    ExpenseSplit,
    GroupExpense,
    PeerDebt,
    Settlement,
)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin for Contact model."""

    list_display = [
        "name",
        "email",
        "phone",
        "status",
        "linked_user",
        "share_status",
        "tenant_id",
        "created_at",
    ]
    list_filter = ["status", "share_status", "created_at"]
    search_fields = ["name", "email", "phone"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]

    fieldsets = [
        (None, {"fields": ["id", "tenant_id", "name"]}),
        ("Contact Info", {"fields": ["email", "phone", "avatar_url", "notes"]}),
        ("Status", {"fields": ["status", "linked_user", "share_status"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(ContactGroup)
class ContactGroupAdmin(admin.ModelAdmin):
    """Admin for ContactGroup model."""

    list_display = ["name", "member_count", "tenant_id", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "created_at", "updated_at", "member_count"]
    filter_horizontal = ["members"]
    ordering = ["-created_at"]

    fieldsets = [
        (None, {"fields": ["id", "tenant_id", "name", "description"]}),
        ("Members", {"fields": ["members", "member_count"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(PeerDebt)
class PeerDebtAdmin(admin.ModelAdmin):
    """Admin for PeerDebt model."""

    list_display = [
        "contact",
        "direction",
        "amount",
        "currency_code",
        "settled_amount",
        "remaining_amount",
        "status",
        "debt_date",
        "due_date",
        "tenant_id",
    ]
    list_filter = ["direction", "status", "currency_code", "debt_date"]
    search_fields = ["contact__name", "description"]
    readonly_fields = ["id", "remaining_amount", "created_at", "updated_at"]
    raw_id_fields = ["contact"]
    ordering = ["-debt_date"]

    fieldsets = [
        (None, {"fields": ["id", "tenant_id", "contact"]}),
        (
            "Debt Details",
            {
                "fields": [
                    "direction",
                    "amount",
                    "currency_code",
                    "settled_amount",
                    "remaining_amount",
                ]
            },
        ),
        ("Dates", {"fields": ["debt_date", "due_date"]}),
        ("Info", {"fields": ["description", "notes", "status"]}),
        ("Links", {"fields": ["linked_transaction_id"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(ExpenseGroup)
class ExpenseGroupAdmin(admin.ModelAdmin):
    """Admin for ExpenseGroup model."""

    list_display = [
        "name",
        "total_members",
        "default_currency",
        "include_self",
        "tenant_id",
        "created_at",
    ]
    list_filter = ["default_currency", "include_self", "created_at"]
    search_fields = ["name", "description"]
    readonly_fields = ["id", "total_members", "created_at", "updated_at"]
    filter_horizontal = ["member_contacts"]
    ordering = ["-created_at"]

    fieldsets = [
        (None, {"fields": ["id", "tenant_id", "name", "description"]}),
        (
            "Settings",
            {"fields": ["default_currency", "include_self", "total_members"]},
        ),
        ("Members", {"fields": ["member_contacts"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


class ExpenseSplitInline(admin.TabularInline):
    """Inline admin for ExpenseSplit."""

    model = ExpenseSplit
    extra = 0
    readonly_fields = ["id", "remaining_amount"]
    raw_id_fields = ["contact"]


@admin.register(GroupExpense)
class GroupExpenseAdmin(admin.ModelAdmin):
    """Admin for GroupExpense model."""

    list_display = [
        "description",
        "total_amount",
        "currency_code",
        "paid_by_owner",
        "paid_by_contact",
        "split_method",
        "status",
        "expense_date",
        "tenant_id",
    ]
    list_filter = ["status", "split_method", "currency_code", "expense_date"]
    search_fields = ["description"]
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["group", "paid_by_contact"]
    inlines = [ExpenseSplitInline]
    ordering = ["-expense_date"]

    fieldsets = [
        (None, {"fields": ["id", "tenant_id", "group"]}),
        (
            "Expense Details",
            {
                "fields": [
                    "description",
                    "total_amount",
                    "currency_code",
                    "expense_date",
                ]
            },
        ),
        ("Payment", {"fields": ["paid_by_owner", "paid_by_contact"]}),
        ("Split", {"fields": ["split_method", "status"]}),
        ("Notes", {"fields": ["notes"]}),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    """Admin for ExpenseSplit model."""

    list_display = [
        "expense",
        "contact",
        "is_owner",
        "share_amount",
        "settled_amount",
        "remaining_amount",
        "status",
    ]
    list_filter = ["status", "is_owner"]
    search_fields = ["expense__description", "contact__name"]
    readonly_fields = ["id", "remaining_amount"]
    raw_id_fields = ["expense", "contact"]

    fieldsets = [
        (None, {"fields": ["id", "expense"]}),
        ("Participant", {"fields": ["contact", "is_owner"]}),
        (
            "Amounts",
            {"fields": ["share_amount", "settled_amount", "remaining_amount"]},
        ),
        ("Status", {"fields": ["status"]}),
    ]


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    """Admin for Settlement model."""

    list_display = [
        "id",
        "from_display",
        "to_display",
        "amount",
        "currency_code",
        "method",
        "settlement_date",
        "tenant_id",
    ]
    list_filter = ["method", "currency_code", "settlement_date"]
    search_fields = ["from_contact__name", "to_contact__name", "notes"]
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["from_contact", "to_contact"]
    filter_horizontal = ["linked_debts", "linked_splits"]
    ordering = ["-settlement_date"]

    fieldsets = [
        (None, {"fields": ["id", "tenant_id"]}),
        (
            "From",
            {"fields": ["from_is_owner", "from_contact"]},
        ),
        (
            "To",
            {"fields": ["to_is_owner", "to_contact"]},
        ),
        (
            "Payment",
            {"fields": ["amount", "currency_code", "method", "settlement_date"]},
        ),
        ("Links", {"fields": ["linked_debts", "linked_splits"]}),
        ("Notes", {"fields": ["notes"]}),
        ("Timestamps", {"fields": ["created_at"]}),
    ]

    @admin.display(description="From")
    def from_display(self, obj):
        """Display from party."""
        if obj.from_is_owner:
            return "Owner"
        return str(obj.from_contact) if obj.from_contact else "-"

    @admin.display(description="To")
    def to_display(self, obj):
        """Display to party."""
        if obj.to_is_owner:
            return "Owner"
        return str(obj.to_contact) if obj.to_contact else "-"
