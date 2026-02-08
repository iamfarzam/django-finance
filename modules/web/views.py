"""Web views for Django Finance.

These views render HTML templates for the web interface.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from modules.finance.infrastructure.models import Account, Category, Transaction
from modules.social.infrastructure.models import (
    Contact,
    ContactGroup,
    ExpenseGroup,
    GroupExpense,
    PeerDebt,
    Settlement,
)


# =============================================================================
# Dashboard
# =============================================================================


class ReactDashboardView(LoginRequiredMixin, TemplateView):
    """React-based dashboard served as static export.

    This view renders the Django template wrapper that loads the
    Next.js static export from /static/react/.
    """

    template_name = "react/dashboard.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard with financial overview."""

    template_name = "finance/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add dashboard data to context."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tenant_id = user.id

        # Account stats
        accounts = Account.objects.filter(tenant_id=tenant_id, status="active")
        context["accounts_count"] = accounts.count()

        # Calculate totals
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")

        for account in accounts:
            balance = account.calculate_balance()
            if account.account_type in ["checking", "savings", "investment", "cash"]:
                total_assets += balance
            elif account.account_type in ["credit_card", "loan"]:
                total_liabilities += balance

        context["total_assets"] = f"${total_assets:,.2f}"
        context["total_liabilities"] = f"${total_liabilities:,.2f}"
        net_worth = total_assets - total_liabilities
        context["net_worth"] = f"${net_worth:,.2f}"
        context["net_worth_positive"] = net_worth >= 0

        # This month's transactions
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        transactions = Transaction.objects.filter(
            tenant_id=tenant_id,
            transaction_date__gte=start_of_month,
        )
        context["transactions_this_month"] = transactions.count()

        # Recent transactions (last 5)
        recent_txns = Transaction.objects.filter(tenant_id=tenant_id).select_related(
            "account"
        ).order_by("-transaction_date", "-created_at")[:5]

        context["recent_transactions"] = [
            {
                "description": txn.description or txn.transaction_type.title(),
                "type": txn.transaction_type,
                "amount": f"${txn.amount:,.2f}",
                "account_name": txn.account.name if txn.account else "Unknown",
                "date": txn.transaction_date,
            }
            for txn in recent_txns
        ]

        # Contacts count
        context["contacts_count"] = Contact.objects.filter(
            tenant_id=tenant_id,
            status="active",
        ).count()

        # Active debts count
        context["active_debts_count"] = PeerDebt.objects.filter(
            tenant_id=tenant_id,
            status="active",
        ).count()

        # Social finance summary
        others_owe = Decimal("0")
        you_owe = Decimal("0")

        debts = PeerDebt.objects.filter(tenant_id=tenant_id, status="active")
        for debt in debts:
            if debt.direction == "lent":
                others_owe += debt.remaining_amount
            else:
                you_owe += debt.remaining_amount

        context["others_owe_you"] = f"${others_owe:,.2f}"
        context["you_owe_others"] = f"${you_owe:,.2f}"

        # Recent social activity
        recent_debts = PeerDebt.objects.filter(tenant_id=tenant_id).select_related(
            "contact"
        ).order_by("-created_at")[:5]

        context["social_activity"] = [
            {
                "contact_name": debt.contact.name if debt.contact else "Unknown",
                "description": debt.reason or "Debt",
                "amount": f"${debt.remaining_amount:,.2f}",
                "direction": "they_owe" if debt.direction == "lent" else "you_owe",
            }
            for debt in recent_debts
        ]

        return context


# =============================================================================
# Accounts
# =============================================================================


class AccountListView(LoginRequiredMixin, ListView):
    """List all accounts."""

    template_name = "finance/accounts/list.html"
    context_object_name = "accounts"
    paginate_by = 20

    def get_queryset(self):
        """Get accounts for current user."""
        return Account.objects.filter(
            tenant_id=self.request.user.id,
            status="active",
        ).order_by("name")


class AccountDetailView(LoginRequiredMixin, DetailView):
    """Account detail view."""

    template_name = "finance/accounts/detail.html"
    context_object_name = "account"

    def get_queryset(self):
        """Get accounts for current user."""
        return Account.objects.filter(tenant_id=self.request.user.id)


class AccountCreateView(LoginRequiredMixin, CreateView):
    """Create a new account."""

    template_name = "finance/accounts/form.html"
    model = Account
    fields = ["name", "account_type", "currency_code", "description"]
    success_url = reverse_lazy("web:accounts_list")

    def form_valid(self, form):
        """Set tenant before saving."""
        form.instance.tenant_id = self.request.user.id
        return super().form_valid(form)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    """Update an account."""

    template_name = "finance/accounts/form.html"
    model = Account
    fields = ["name", "description"]
    success_url = reverse_lazy("web:accounts_list")

    def get_queryset(self):
        """Get accounts for current user."""
        return Account.objects.filter(tenant_id=self.request.user.id)


# =============================================================================
# Transactions
# =============================================================================


class TransactionListView(LoginRequiredMixin, ListView):
    """List all transactions."""

    template_name = "finance/transactions/list.html"
    context_object_name = "transactions"
    paginate_by = 50

    def get_queryset(self):
        """Get transactions for current user."""
        return Transaction.objects.filter(
            tenant_id=self.request.user.id,
        ).select_related("account", "category").order_by(
            "-transaction_date", "-created_at"
        )


class TransactionDetailView(LoginRequiredMixin, DetailView):
    """Transaction detail view."""

    template_name = "finance/transactions/detail.html"
    context_object_name = "transaction"

    def get_queryset(self):
        """Get transactions for current user."""
        return Transaction.objects.filter(
            tenant_id=self.request.user.id
        ).select_related("account", "category")


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create a new transaction."""

    template_name = "finance/transactions/form.html"
    model = Transaction
    fields = [
        "account",
        "transaction_type",
        "amount",
        "description",
        "category",
        "transaction_date",
    ]
    success_url = reverse_lazy("web:transactions_list")

    def get_form(self, form_class=None):
        """Limit account and category choices to current user."""
        form = super().get_form(form_class)
        form.fields["account"].queryset = Account.objects.filter(
            tenant_id=self.request.user.id, status="active"
        )
        form.fields["category"].queryset = Category.objects.filter(
            tenant_id=self.request.user.id
        )
        form.fields["category"].required = False
        return form

    def form_valid(self, form):
        """Set tenant before saving."""
        form.instance.tenant_id = self.request.user.id
        form.instance.currency_code = form.instance.account.currency_code
        return super().form_valid(form)


# =============================================================================
# Contacts
# =============================================================================


class ContactListView(LoginRequiredMixin, ListView):
    """List all contacts."""

    template_name = "social/contacts/list.html"
    context_object_name = "contacts"
    paginate_by = 50

    def get_queryset(self):
        """Get contacts for current user."""
        return Contact.objects.filter(
            tenant_id=self.request.user.id,
            status="active",
        ).order_by("name")


class ContactDetailView(LoginRequiredMixin, DetailView):
    """Contact detail view."""

    template_name = "social/contacts/detail.html"
    context_object_name = "contact"

    def get_queryset(self):
        """Get contacts for current user."""
        return Contact.objects.filter(tenant_id=self.request.user.id)

    def get_context_data(self, **kwargs):
        """Add related debts and balances."""
        context = super().get_context_data(**kwargs)
        contact = self.object

        # Get debts with this contact
        context["debts"] = PeerDebt.objects.filter(
            tenant_id=self.request.user.id,
            contact=contact,
        ).order_by("-created_at")

        return context


class ContactCreateView(LoginRequiredMixin, CreateView):
    """Create a new contact."""

    template_name = "social/contacts/form.html"
    model = Contact
    fields = ["name", "email", "phone", "notes"]
    success_url = reverse_lazy("web:contacts_list")

    def form_valid(self, form):
        """Set tenant before saving."""
        form.instance.tenant_id = self.request.user.id
        return super().form_valid(form)


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    """Update a contact."""

    template_name = "social/contacts/form.html"
    model = Contact
    fields = ["name", "email", "phone", "notes"]
    success_url = reverse_lazy("web:contacts_list")

    def get_queryset(self):
        """Get contacts for current user."""
        return Contact.objects.filter(tenant_id=self.request.user.id)


# =============================================================================
# Peer Debts
# =============================================================================


class DebtListView(LoginRequiredMixin, ListView):
    """List all peer debts."""

    template_name = "social/debts/list.html"
    context_object_name = "debts"
    paginate_by = 50

    def get_queryset(self):
        """Get debts for current user."""
        return PeerDebt.objects.filter(
            tenant_id=self.request.user.id,
        ).select_related("contact").order_by("-created_at")

    def get_context_data(self, **kwargs):
        """Add summary stats."""
        context = super().get_context_data(**kwargs)

        active_debts = PeerDebt.objects.filter(
            tenant_id=self.request.user.id,
            status="active",
        )

        lent_total = sum(
            d.remaining_amount for d in active_debts if d.direction == "lent"
        )
        borrowed_total = sum(
            d.remaining_amount for d in active_debts if d.direction == "borrowed"
        )

        context["lent_total"] = f"${lent_total:,.2f}"
        context["borrowed_total"] = f"${borrowed_total:,.2f}"
        context["net_balance"] = f"${lent_total - borrowed_total:,.2f}"

        return context


class DebtDetailView(LoginRequiredMixin, DetailView):
    """Debt detail view."""

    template_name = "social/debts/detail.html"
    context_object_name = "debt"

    def get_queryset(self):
        """Get debts for current user."""
        return PeerDebt.objects.filter(
            tenant_id=self.request.user.id
        ).select_related("contact")


class DebtCreateView(LoginRequiredMixin, CreateView):
    """Create a new debt."""

    template_name = "social/debts/form.html"
    model = PeerDebt
    fields = ["contact", "direction", "amount", "currency_code", "reason", "debt_date"]
    success_url = reverse_lazy("web:debts_list")

    def get_form(self, form_class=None):
        """Limit contact choices to current user."""
        form = super().get_form(form_class)
        form.fields["contact"].queryset = Contact.objects.filter(
            tenant_id=self.request.user.id, status="active"
        )
        return form

    def form_valid(self, form):
        """Set tenant and remaining amount before saving."""
        form.instance.tenant_id = self.request.user.id
        form.instance.remaining_amount = form.instance.amount
        return super().form_valid(form)


# =============================================================================
# Expense Groups
# =============================================================================


class GroupListView(LoginRequiredMixin, ListView):
    """List all expense groups."""

    template_name = "social/groups/list.html"
    context_object_name = "groups"
    paginate_by = 20

    def get_queryset(self):
        """Get groups for current user."""
        return ExpenseGroup.objects.filter(
            tenant_id=self.request.user.id,
        ).order_by("-created_at")


class GroupDetailView(LoginRequiredMixin, DetailView):
    """Group detail view."""

    template_name = "social/groups/detail.html"
    context_object_name = "group"

    def get_queryset(self):
        """Get groups for current user."""
        return ExpenseGroup.objects.filter(tenant_id=self.request.user.id)

    def get_context_data(self, **kwargs):
        """Add expenses and balances."""
        context = super().get_context_data(**kwargs)
        group = self.object

        context["expenses"] = GroupExpense.objects.filter(
            group=group
        ).order_by("-expense_date", "-created_at")

        return context


class GroupCreateView(LoginRequiredMixin, CreateView):
    """Create a new expense group."""

    template_name = "social/groups/form.html"
    model = ExpenseGroup
    fields = ["name", "description", "default_currency"]
    success_url = reverse_lazy("web:groups_list")

    def form_valid(self, form):
        """Set tenant before saving."""
        form.instance.tenant_id = self.request.user.id
        return super().form_valid(form)


# =============================================================================
# Settlements
# =============================================================================


class SettlementListView(LoginRequiredMixin, ListView):
    """List all settlements."""

    template_name = "social/settlements/list.html"
    context_object_name = "settlements"
    paginate_by = 50

    def get_queryset(self):
        """Get settlements for current user."""
        return Settlement.objects.filter(
            tenant_id=self.request.user.id,
        ).select_related("contact").order_by("-settlement_date", "-created_at")


class SettlementCreateView(LoginRequiredMixin, CreateView):
    """Create a new settlement."""

    template_name = "social/settlements/form.html"
    model = Settlement
    fields = ["contact", "amount", "currency_code", "from_is_owner", "method", "notes"]
    success_url = reverse_lazy("web:settlements_list")

    def get_form(self, form_class=None):
        """Limit contact choices to current user."""
        form = super().get_form(form_class)
        form.fields["contact"].queryset = Contact.objects.filter(
            tenant_id=self.request.user.id, status="active"
        )
        return form

    def form_valid(self, form):
        """Set tenant before saving."""
        form.instance.tenant_id = self.request.user.id
        return super().form_valid(form)


# =============================================================================
# Balances
# =============================================================================


class BalancesSummaryView(LoginRequiredMixin, TemplateView):
    """Summary of all balances with contacts."""

    template_name = "social/balances/summary.html"

    def get_context_data(self, **kwargs):
        """Calculate balances per contact."""
        context = super().get_context_data(**kwargs)
        tenant_id = self.request.user.id

        contacts = Contact.objects.filter(
            tenant_id=tenant_id,
            status="active",
        )

        balances = []
        for contact in contacts:
            debts = PeerDebt.objects.filter(
                tenant_id=tenant_id,
                contact=contact,
                status="active",
            )

            lent = sum(d.remaining_amount for d in debts if d.direction == "lent")
            borrowed = sum(
                d.remaining_amount for d in debts if d.direction == "borrowed"
            )
            net = lent - borrowed

            if net != 0:
                balances.append({
                    "contact": contact,
                    "net_balance": net,
                    "direction": "they_owe" if net > 0 else "you_owe",
                    "amount": f"${abs(net):,.2f}",
                })

        context["balances"] = sorted(
            balances, key=lambda x: abs(x["net_balance"]), reverse=True
        )

        return context


# =============================================================================
# User Profile & Settings
# =============================================================================


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile page."""

    template_name = "accounts/profile.html"


class SettingsView(LoginRequiredMixin, TemplateView):
    """User settings page."""

    template_name = "accounts/settings.html"


# =============================================================================
# Notifications
# =============================================================================


class NotificationsListView(LoginRequiredMixin, TemplateView):
    """Notifications list page."""

    template_name = "notifications/list.html"


# =============================================================================
# Net Worth
# =============================================================================


class NetWorthView(LoginRequiredMixin, TemplateView):
    """Net worth details page."""

    template_name = "finance/net_worth.html"

    def get_context_data(self, **kwargs):
        """Calculate net worth details."""
        context = super().get_context_data(**kwargs)
        tenant_id = self.request.user.id

        accounts = Account.objects.filter(tenant_id=tenant_id, status="active")

        assets = []
        liabilities = []

        for account in accounts:
            balance = account.calculate_balance()
            item = {
                "name": account.name,
                "type": account.account_type,
                "balance": balance,
                "formatted": f"${balance:,.2f}",
            }

            if account.account_type in ["checking", "savings", "investment", "cash"]:
                assets.append(item)
            elif account.account_type in ["credit_card", "loan"]:
                liabilities.append(item)

        context["assets"] = assets
        context["liabilities"] = liabilities
        context["total_assets"] = sum(a["balance"] for a in assets)
        context["total_liabilities"] = sum(l["balance"] for l in liabilities)
        context["net_worth"] = context["total_assets"] - context["total_liabilities"]

        return context
