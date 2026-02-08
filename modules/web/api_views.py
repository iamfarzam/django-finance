"""API views for the web module.

These views provide REST API endpoints for the React dashboard.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.finance.infrastructure.models import Account, Transaction
from modules.social.infrastructure.models import Contact, PeerDebt


class DashboardAPIView(APIView):
    """Aggregated dashboard data endpoint for React frontend.

    Returns all data needed for the dashboard in a single request:
    - User info
    - Net worth (assets, liabilities)
    - Stats (accounts, transactions, contacts, debts)
    - Recent transactions
    - Social finance summary
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get dashboard data for authenticated user."""
        user = request.user
        tenant_id = user.id

        # Build response data
        data = {
            "user": self._get_user_data(user),
            "net_worth": self._get_net_worth(tenant_id),
            "stats": self._get_stats(tenant_id),
            "recent_transactions": self._get_recent_transactions(tenant_id),
            "social": self._get_social_summary(tenant_id),
        }

        return Response(data, status=status.HTTP_200_OK)

    def _get_user_data(self, user) -> dict:
        """Get user information."""
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}".strip() or user.email,
        }

    def _get_net_worth(self, tenant_id) -> dict:
        """Calculate net worth from accounts."""
        accounts = Account.objects.filter(tenant_id=tenant_id, is_active=True)

        total_assets = Decimal("0")
        total_liabilities = Decimal("0")

        for account in accounts:
            balance = account.calculate_balance()
            if account.account_type in ["checking", "savings", "investment", "cash"]:
                total_assets += balance
            elif account.account_type in ["credit_card", "loan"]:
                total_liabilities += abs(balance)

        net_worth = total_assets - total_liabilities

        return {
            "total_assets": float(total_assets),
            "total_liabilities": float(total_liabilities),
            "net_worth": float(net_worth),
            "currency": "USD",
        }

    def _get_stats(self, tenant_id) -> dict:
        """Get dashboard statistics."""
        # Accounts count
        accounts_count = Account.objects.filter(
            tenant_id=tenant_id, is_active=True
        ).count()

        # This month's transactions
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        transactions_count = Transaction.objects.filter(
            tenant_id=tenant_id,
            transaction_date__gte=start_of_month,
        ).count()

        # Contacts count
        contacts_count = Contact.objects.filter(
            tenant_id=tenant_id,
            is_archived=False,
        ).count()

        # Active debts count
        active_debts_count = PeerDebt.objects.filter(
            tenant_id=tenant_id,
            status="active",
        ).count()

        return {
            "accounts_count": accounts_count,
            "transactions_count": transactions_count,
            "contacts_count": contacts_count,
            "active_debts_count": active_debts_count,
        }

    def _get_recent_transactions(self, tenant_id) -> list:
        """Get recent transactions."""
        recent_txns = (
            Transaction.objects.filter(tenant_id=tenant_id)
            .select_related("account", "category")
            .order_by("-transaction_date", "-created_at")[:5]
        )

        return [
            {
                "id": str(txn.id),
                "description": txn.description or txn.transaction_type.title(),
                "amount": float(txn.amount),
                "transaction_type": txn.transaction_type,
                "date": txn.transaction_date.isoformat(),
                "account_name": txn.account.name if txn.account else None,
                "category_name": txn.category.name if txn.category else None,
            }
            for txn in recent_txns
        ]

    def _get_social_summary(self, tenant_id) -> dict:
        """Get social finance summary."""
        others_owe = Decimal("0")
        you_owe = Decimal("0")

        debts = PeerDebt.objects.filter(tenant_id=tenant_id, status="active")
        for debt in debts:
            if debt.direction == "lent":
                others_owe += debt.remaining_amount
            else:
                you_owe += debt.remaining_amount

        return {
            "total_they_owe": float(others_owe),
            "total_you_owe": float(you_owe),
            "net_balance": float(others_owe - you_owe),
            "currency": "USD",
        }
