"""URL routing for the social finance module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.social.interfaces.views import (
    BalanceViewSet,
    ContactGroupViewSet,
    ContactViewSet,
    ExpenseGroupViewSet,
    GroupExpenseViewSet,
    PeerDebtViewSet,
    SettlementViewSet,
)

app_name = "social"

router = DefaultRouter()
router.register(r"contacts", ContactViewSet, basename="contact")
router.register(r"contact-groups", ContactGroupViewSet, basename="contact-group")
router.register(r"peer-debts", PeerDebtViewSet, basename="peer-debt")
router.register(r"expense-groups", ExpenseGroupViewSet, basename="expense-group")
router.register(r"group-expenses", GroupExpenseViewSet, basename="group-expense")
router.register(r"settlements", SettlementViewSet, basename="settlement")
router.register(r"balances", BalanceViewSet, basename="balance")

urlpatterns = [
    path("", include(router.urls)),
]
