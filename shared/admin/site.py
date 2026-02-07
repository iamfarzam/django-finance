"""Custom admin site for Django Finance platform.

This module provides a branded admin site with custom styling,
dashboard widgets, and enhanced functionality.
"""

from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path


class FinanceAdminSite(admin.AdminSite):
    """Custom admin site with branding and enhanced features.

    Provides:
    - Custom branding and titles
    - Enhanced dashboard with quick stats
    - Custom CSS styling
    - Financial summary widgets
    """

    # Branding
    site_header = "Django Finance Administration"
    site_title = "Django Finance"
    index_title = "Financial Management Dashboard"

    # Custom template for index
    index_template = "admin/finance_index.html"

    def get_urls(self):
        """Add custom admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "dashboard/stats/",
                self.admin_view(self.dashboard_stats_view),
                name="dashboard_stats",
            ),
            path(
                "audit-logs/",
                self.admin_view(self.audit_logs_view),
                name="audit_logs",
            ),
        ]
        return custom_urls + urls

    def dashboard_stats_view(self, request):
        """Display financial statistics dashboard."""
        from django.db.models import Count, Sum
        from django.utils import timezone

        from modules.finance.infrastructure.models import Account, Transaction
        from modules.social.infrastructure.models import PeerDebt, Settlement

        # Get stats for the current user's tenant
        tenant_id = getattr(request.user, "tenant_id", None)

        context = {
            **self.each_context(request),
            "title": "Dashboard Statistics",
        }

        if tenant_id:
            # Account stats
            accounts = Account.objects.filter(tenant_id=tenant_id)
            context["total_accounts"] = accounts.count()
            context["active_accounts"] = accounts.filter(status="active").count()

            # Transaction stats (last 30 days)
            thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
            recent_transactions = Transaction.objects.filter(
                tenant_id=tenant_id,
                transaction_date__gte=thirty_days_ago,
            )
            context["recent_transaction_count"] = recent_transactions.count()

            # Credits and debits
            credits = recent_transactions.filter(transaction_type="credit").aggregate(
                total=Sum("amount")
            )
            debits = recent_transactions.filter(transaction_type="debit").aggregate(
                total=Sum("amount")
            )
            context["total_credits"] = credits["total"] or 0
            context["total_debits"] = debits["total"] or 0

            # Debt stats
            debts = PeerDebt.objects.filter(tenant_id=tenant_id)
            context["total_debts"] = debts.count()
            context["pending_debts"] = debts.filter(status="pending").count()

            # Settlement stats
            settlements = Settlement.objects.filter(tenant_id=tenant_id)
            context["total_settlements"] = settlements.count()

        return TemplateResponse(request, "admin/dashboard_stats.html", context)

    def audit_logs_view(self, request):
        """Display audit logs (from structlog output)."""
        context = {
            **self.each_context(request),
            "title": "Audit Logs",
            "subtitle": "View recent audit events from the system logs.",
        }
        return TemplateResponse(request, "admin/audit_logs.html", context)

    def each_context(self, request):
        """Add custom context to all admin pages."""
        context = super().each_context(request)
        context["finance_admin"] = True
        return context


# Create the custom admin site instance
finance_admin_site = FinanceAdminSite(name="finance_admin")
