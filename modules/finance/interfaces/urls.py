"""URL routing for finance module API."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from modules.finance.interfaces.views import (
    AccountViewSet,
    AssetViewSet,
    CategoryViewSet,
    LiabilityViewSet,
    LoanViewSet,
    ReportsViewSet,
    TransactionViewSet,
    TransferViewSet,
)

app_name = "finance"

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"accounts", AccountViewSet, basename="account")
router.register(r"transactions", TransactionViewSet, basename="transaction")
router.register(r"transfers", TransferViewSet, basename="transfer")
router.register(r"assets", AssetViewSet, basename="asset")
router.register(r"liabilities", LiabilityViewSet, basename="liability")
router.register(r"loans", LoanViewSet, basename="loan")
router.register(r"reports", ReportsViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
]
