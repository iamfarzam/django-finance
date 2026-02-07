"""Django admin configuration for the social finance module.

Enhanced admin with:
- Tenant-scoped filtering
- Bulk actions for settlements and debt management
- Inline editing for expense splits
- Enhanced displays with balance calculations
- Export capabilities
"""

from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html

from modules.social.infrastructure.models import (
    Contact,
    ContactGroup,
    ExpenseGroup,
    ExpenseSplit,
    GroupExpense,
    PeerDebt,
    Settlement,
)
from shared.admin.base import AuditLogMixin, ExportMixin, TenantScopedAdmin


# =============================================================================
# Inline Admin Classes
# =============================================================================


class PeerDebtInline(admin.TabularInline):
    """Inline for viewing debts related to a contact."""

    model = PeerDebt
    extra = 0
    max_num = 5
    readonly_fields = ["direction", "amount", "currency_code", "remaining_amount", "status", "debt_date"]
    fields = readonly_fields
    can_delete = False
    show_change_link = True

    def get_queryset(self, request):
        """Limit to recent debts."""
        qs = super().get_queryset(request)
        return qs.order_by("-debt_date")[:5]

    def has_add_permission(self, request, obj=None):
        return False


class ExpenseSplitInline(admin.TabularInline):
    """Inline admin for ExpenseSplit with enhanced display."""

    model = ExpenseSplit
    extra = 1
    readonly_fields = ["remaining_amount", "status_badge"]
    fields = ["contact", "is_owner", "share_amount", "settled_amount", "remaining_amount", "status_badge"]
    raw_id_fields = ["contact"]

    @admin.display(description="Status")
    def status_badge(self, obj):
        if not obj.pk:
            return "-"
        colors = {
            "pending": "#f59e0b",
            "partial": "#3b82f6",
            "settled": "#10b981",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display() if hasattr(obj, "get_status_display") else obj.status,
        )


class SettlementDebtInline(admin.TabularInline):
    """Inline for viewing debts linked to a settlement."""

    model = Settlement.linked_debts.through
    extra = 0
    verbose_name = "Linked Debt"
    verbose_name_plural = "Linked Debts"


# =============================================================================
# Model Admin Classes
# =============================================================================


@admin.register(Contact)
class ContactAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin for Contact model with enhanced features."""

    list_display = [
        "name",
        "email",
        "phone",
        "status_badge",
        "share_status_badge",
        "linked_user",
        "debt_summary",
        "created_at",
    ]
    list_filter = ["status", "share_status", "created_at"]
    search_fields = ["name", "email", "phone", "notes"]
    ordering = ["-created_at"]
    list_per_page = 25
    readonly_fields = ["id", "tenant_id", "created_at", "updated_at"]
    inlines = [PeerDebtInline]

    fieldsets = [
        (None, {"fields": ["name", "tenant_id"]}),
        ("Contact Info", {"fields": ["email", "phone", "avatar_url", "notes"]}),
        ("Status", {"fields": ["status", "linked_user", "share_status"]}),
        (
            "System",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["activate_contacts", "deactivate_contacts", "export_as_csv"]

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "active": "#10b981",
            "inactive": "#6b7280",
            "blocked": "#ef4444",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Share Status")
    def share_status_badge(self, obj):
        colors = {
            "not_shared": "#6b7280",
            "pending": "#f59e0b",
            "accepted": "#10b981",
        }
        color = colors.get(obj.share_status, "#6b7280")
        return format_html(
            '<span style="color: {}; font-weight: 500;">{}</span>',
            color,
            obj.get_share_status_display(),
        )

    @admin.display(description="Debt Balance")
    def debt_summary(self, obj):
        """Calculate total debt balance with this contact."""
        debts = PeerDebt.objects.filter(contact=obj)
        lent = debts.filter(direction="lent").aggregate(Sum("remaining_amount"))["remaining_amount__sum"] or 0
        borrowed = debts.filter(direction="borrowed").aggregate(Sum("remaining_amount"))["remaining_amount__sum"] or 0
        balance = lent - borrowed
        if balance > 0:
            return format_html('<span style="color: #10b981;">+{}</span>', balance)
        elif balance < 0:
            return format_html('<span style="color: #ef4444;">{}</span>', balance)
        return format_html('<span style="color: #6b7280;">0</span>')

    @admin.action(description="Activate selected contacts")
    def activate_contacts(self, request, queryset):
        count = queryset.update(status="active")
        self.message_user(request, f"Activated {count} contacts.")

    @admin.action(description="Deactivate selected contacts")
    def deactivate_contacts(self, request, queryset):
        count = queryset.update(status="inactive")
        self.message_user(request, f"Deactivated {count} contacts.")


@admin.register(ContactGroup)
class ContactGroupAdmin(TenantScopedAdmin, ExportMixin):
    """Admin for ContactGroup model."""

    list_display = ["name", "member_count", "description_short", "tenant_id", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    ordering = ["-created_at"]
    list_per_page = 25
    readonly_fields = ["id", "created_at", "updated_at", "member_count"]
    filter_horizontal = ["members"]

    fieldsets = [
        (None, {"fields": ["name", "description", "tenant_id"]}),
        ("Members", {"fields": ["members", "member_count"]}),
        (
            "System",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Description")
    def description_short(self, obj):
        if obj.description and len(obj.description) > 40:
            return f"{obj.description[:40]}..."
        return obj.description or "-"


@admin.register(PeerDebt)
class PeerDebtAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin for PeerDebt model with enhanced features."""

    list_display = [
        "contact_link",
        "direction_badge",
        "amount_display",
        "settled_display",
        "remaining_display",
        "status_badge",
        "debt_date",
        "due_date_display",
    ]
    list_filter = ["direction", "status", "currency_code", "debt_date"]
    search_fields = ["contact__name", "description", "notes"]
    ordering = ["-debt_date"]
    list_per_page = 25
    date_hierarchy = "debt_date"
    readonly_fields = ["id", "remaining_amount", "created_at", "updated_at"]
    raw_id_fields = ["contact"]
    autocomplete_fields = ["contact"]

    fieldsets = [
        (None, {"fields": ["contact", "tenant_id"]}),
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
        (
            "Links",
            {
                "fields": ["linked_transaction_id"],
                "classes": ["collapse"],
            },
        ),
        (
            "System",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["mark_settled", "mark_partially_paid", "mark_pending", "export_as_csv"]

    @admin.display(description="Contact")
    def contact_link(self, obj):
        return format_html(
            '<a href="/admin/social/contact/{}/change/">{}</a>',
            obj.contact_id,
            obj.contact.name,
        )

    @admin.display(description="Direction")
    def direction_badge(self, obj):
        if obj.direction == "lent":
            return format_html(
                '<span style="color: #10b981; font-weight: 600;">&#8593; Lent</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: 600;">&#8595; Borrowed</span>'
        )

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency_code}"

    @admin.display(description="Settled")
    def settled_display(self, obj):
        if obj.settled_amount > 0:
            return format_html(
                '<span style="color: #3b82f6;">{}</span>',
                obj.settled_amount,
            )
        return "-"

    @admin.display(description="Remaining")
    def remaining_display(self, obj):
        if obj.remaining_amount > 0:
            return format_html(
                '<span style="color: #f59e0b; font-weight: 600;">{}</span>',
                obj.remaining_amount,
            )
        return format_html('<span style="color: #10b981;">Settled</span>')

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending": "#f59e0b",
            "partial": "#3b82f6",
            "settled": "#10b981",
            "cancelled": "#6b7280",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Due Date")
    def due_date_display(self, obj):
        if not obj.due_date:
            return "-"
        if obj.due_date < timezone.now().date() and obj.status == "pending":
            return format_html(
                '<span style="color: #ef4444; font-weight: 600;">{} (Overdue)</span>',
                obj.due_date,
            )
        return obj.due_date

    @admin.action(description="Mark as fully settled")
    def mark_settled(self, request, queryset):
        for debt in queryset:
            debt.settled_amount = debt.amount
            debt.status = "settled"
            debt.save()
        self.message_user(request, f"Marked {queryset.count()} debts as settled.", messages.SUCCESS)

    @admin.action(description="Mark as partially paid (50%)")
    def mark_partially_paid(self, request, queryset):
        for debt in queryset.filter(status="pending"):
            debt.settled_amount = debt.amount / 2
            debt.status = "partial"
            debt.save()
        self.message_user(request, f"Marked debts as partially paid.")

    @admin.action(description="Reset to pending")
    def mark_pending(self, request, queryset):
        count = queryset.update(status="pending", settled_amount=Decimal("0.00"))
        self.message_user(request, f"Reset {count} debts to pending.")


@admin.register(ExpenseGroup)
class ExpenseGroupAdmin(TenantScopedAdmin, ExportMixin):
    """Admin for ExpenseGroup model."""

    list_display = [
        "name",
        "total_members",
        "default_currency",
        "include_self",
        "expense_count",
        "total_expenses_display",
        "created_at",
    ]
    list_filter = ["default_currency", "include_self", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["-created_at"]
    list_per_page = 25
    readonly_fields = ["id", "total_members", "created_at", "updated_at"]
    filter_horizontal = ["member_contacts"]

    fieldsets = [
        (None, {"fields": ["name", "description", "tenant_id"]}),
        (
            "Settings",
            {"fields": ["default_currency", "include_self", "total_members"]},
        ),
        ("Members", {"fields": ["member_contacts"]}),
        (
            "System",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="Expenses")
    def expense_count(self, obj):
        count = GroupExpense.objects.filter(group=obj).count()
        return count

    @admin.display(description="Total Amount")
    def total_expenses_display(self, obj):
        total = GroupExpense.objects.filter(group=obj).aggregate(Sum("total_amount"))["total_amount__sum"]
        if total:
            return f"{total} {obj.default_currency}"
        return "-"


@admin.register(GroupExpense)
class GroupExpenseAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin for GroupExpense model."""

    list_display = [
        "description",
        "group_link",
        "total_amount_display",
        "paid_by_display",
        "split_method",
        "status_badge",
        "expense_date",
    ]
    list_filter = ["status", "split_method", "currency_code", "expense_date"]
    search_fields = ["description", "group__name", "notes"]
    ordering = ["-expense_date"]
    list_per_page = 25
    date_hierarchy = "expense_date"
    readonly_fields = ["id", "created_at", "updated_at"]
    raw_id_fields = ["group", "paid_by_contact"]
    inlines = [ExpenseSplitInline]

    fieldsets = [
        (None, {"fields": ["group", "tenant_id"]}),
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
        (
            "System",
            {
                "fields": ["id", "created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    actions = ["mark_settled", "recalculate_splits", "export_as_csv"]

    @admin.display(description="Group")
    def group_link(self, obj):
        return format_html(
            '<a href="/admin/social/expensegroup/{}/change/">{}</a>',
            obj.group_id,
            obj.group.name,
        )

    @admin.display(description="Amount")
    def total_amount_display(self, obj):
        return format_html(
            '<span style="font-weight: 600;">{} {}</span>',
            obj.total_amount,
            obj.currency_code,
        )

    @admin.display(description="Paid By")
    def paid_by_display(self, obj):
        if obj.paid_by_owner:
            return format_html('<span style="color: #3b82f6;">Owner (You)</span>')
        elif obj.paid_by_contact:
            return obj.paid_by_contact.name
        return "-"

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending": "#f59e0b",
            "partial": "#3b82f6",
            "settled": "#10b981",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description="Mark all splits as settled")
    def mark_settled(self, request, queryset):
        for expense in queryset:
            ExpenseSplit.objects.filter(expense=expense).update(
                status="settled",
                settled_amount=models.F("share_amount"),
            )
            expense.status = "settled"
            expense.save()
        self.message_user(request, f"Marked {queryset.count()} expenses as settled.")


@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(TenantScopedAdmin, ExportMixin):
    """Admin for ExpenseSplit model."""

    list_display = [
        "expense_link",
        "contact_display",
        "share_amount_display",
        "settled_amount_display",
        "remaining_amount_display",
        "status_badge",
    ]
    list_filter = ["status", "is_owner"]
    search_fields = ["expense__description", "contact__name"]
    ordering = ["-expense__expense_date"]
    list_per_page = 50
    readonly_fields = ["id", "remaining_amount"]
    raw_id_fields = ["expense", "contact"]

    fieldsets = [
        (None, {"fields": ["expense"]}),
        ("Participant", {"fields": ["contact", "is_owner"]}),
        (
            "Amounts",
            {"fields": ["share_amount", "settled_amount", "remaining_amount"]},
        ),
        ("Status", {"fields": ["status"]}),
    ]

    actions = ["mark_settled", "reset_to_pending"]

    @admin.display(description="Expense")
    def expense_link(self, obj):
        return format_html(
            '<a href="/admin/social/groupexpense/{}/change/">{}</a>',
            obj.expense_id,
            obj.expense.description[:30],
        )

    @admin.display(description="Participant")
    def contact_display(self, obj):
        if obj.is_owner:
            return format_html('<span style="color: #3b82f6; font-weight: 500;">Owner (You)</span>')
        return obj.contact.name if obj.contact else "-"

    @admin.display(description="Share")
    def share_amount_display(self, obj):
        return f"{obj.share_amount}"

    @admin.display(description="Settled")
    def settled_amount_display(self, obj):
        if obj.settled_amount > 0:
            return format_html('<span style="color: #10b981;">{}</span>', obj.settled_amount)
        return "-"

    @admin.display(description="Remaining")
    def remaining_amount_display(self, obj):
        if obj.remaining_amount > 0:
            return format_html('<span style="color: #f59e0b;">{}</span>', obj.remaining_amount)
        return format_html('<span style="color: #10b981;">Settled</span>')

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "pending": "#f59e0b",
            "partial": "#3b82f6",
            "settled": "#10b981",
        }
        color = colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px;">{}</span>',
            color,
            obj.get_status_display() if hasattr(obj, "get_status_display") else obj.status,
        )

    @admin.action(description="Mark as settled")
    def mark_settled(self, request, queryset):
        for split in queryset:
            split.settled_amount = split.share_amount
            split.status = "settled"
            split.save()
        self.message_user(request, f"Marked {queryset.count()} splits as settled.")

    @admin.action(description="Reset to pending")
    def reset_to_pending(self, request, queryset):
        count = queryset.update(status="pending", settled_amount=Decimal("0.00"))
        self.message_user(request, f"Reset {count} splits to pending.")


@admin.register(Settlement)
class SettlementAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    """Admin for Settlement model."""

    list_display = [
        "id_short",
        "from_display",
        "arrow_display",
        "to_display",
        "amount_display",
        "method_badge",
        "settlement_date",
        "linked_items_count",
    ]
    list_filter = ["method", "currency_code", "settlement_date"]
    search_fields = ["from_contact__name", "to_contact__name", "notes"]
    ordering = ["-settlement_date"]
    list_per_page = 25
    date_hierarchy = "settlement_date"
    readonly_fields = ["id", "created_at"]
    raw_id_fields = ["from_contact", "to_contact"]
    filter_horizontal = ["linked_debts", "linked_splits"]

    fieldsets = [
        (None, {"fields": ["tenant_id"]}),
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
        (
            "System",
            {
                "fields": ["id", "created_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    @admin.display(description="ID")
    def id_short(self, obj):
        return str(obj.id)[:8]

    @admin.display(description="From")
    def from_display(self, obj):
        if obj.from_is_owner:
            return format_html('<span style="color: #3b82f6; font-weight: 500;">You</span>')
        return str(obj.from_contact.name) if obj.from_contact else "-"

    @admin.display(description="")
    def arrow_display(self, obj):
        return format_html('<span style="font-size: 18px; color: #10b981;">&#8594;</span>')

    @admin.display(description="To")
    def to_display(self, obj):
        if obj.to_is_owner:
            return format_html('<span style="color: #3b82f6; font-weight: 500;">You</span>')
        return str(obj.to_contact.name) if obj.to_contact else "-"

    @admin.display(description="Amount")
    def amount_display(self, obj):
        return format_html(
            '<span style="color: #10b981; font-weight: 600;">{} {}</span>',
            obj.amount,
            obj.currency_code,
        )

    @admin.display(description="Method")
    def method_badge(self, obj):
        if not obj.method:
            return "-"
        colors = {
            "cash": "#10b981",
            "bank_transfer": "#3b82f6",
            "upi": "#8b5cf6",
            "venmo": "#3b82f6",
            "paypal": "#0070ba",
            "other": "#6b7280",
        }
        color = colors.get(obj.method, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; '
            'border-radius: 10px; font-size: 10px;">{}</span>',
            color,
            obj.get_method_display() if hasattr(obj, "get_method_display") else obj.method,
        )

    @admin.display(description="Linked")
    def linked_items_count(self, obj):
        debt_count = obj.linked_debts.count()
        split_count = obj.linked_splits.count()
        total = debt_count + split_count
        if total > 0:
            return f"{total} items"
        return "-"
