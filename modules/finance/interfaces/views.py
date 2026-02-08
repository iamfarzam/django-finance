"""DRF views for the finance module.

Views handle HTTP requests and delegate to use cases.
They translate between HTTP and application layer DTOs.
"""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shared.permissions import (
    CanCreateAccount,
    HasFeature,
    IsOwner,
    TenantIsolation,
    WithinUsageLimit,
)

from modules.finance.infrastructure.models import (
    Account,
    Asset,
    Category,
    Liability,
    Loan,
    Transaction,
    Transfer,
)
from modules.finance.interfaces.serializers import (
    AccountBalanceSerializer,
    AccountSerializer,
    AssetSerializer,
    CategorySerializer,
    CreateAccountSerializer,
    CreateAssetSerializer,
    CreateCategorySerializer,
    CreateLiabilitySerializer,
    CreateLoanSerializer,
    CreateTransactionSerializer,
    CreateTransferSerializer,
    LiabilitySerializer,
    LoanSerializer,
    NetWorthSerializer,
    RecordLoanPaymentSerializer,
    TransactionSerializer,
    TransferSerializer,
    UpdateAccountSerializer,
    UpdateAssetValueSerializer,
    VoidTransactionSerializer,
)


class TenantScopedViewSet(viewsets.ModelViewSet):
    """Base viewset that scopes queries to the current tenant.

    Supports subscription-based permission configuration:
    - action_features: Map actions to required feature codes
    - action_limits: Map actions to usage limit keys
    """

    permission_classes = [IsAuthenticated, TenantIsolation]
    ordering = ["-created_at"]

    # Map action names to required feature codes
    # e.g., {"export": "export.json", "analytics": "reports.advanced"}
    action_features: dict[str, str] = {}

    # Map action names to usage limit keys
    # e.g., {"create": "accounts_max"}
    action_limits: dict[str, str] = {}

    def get_permissions(self):
        """Add feature/limit permissions based on action mappings."""
        permissions = super().get_permissions()

        # Add feature permission if action is mapped
        if self.action and self.action in self.action_features:
            feature_code = self.action_features[self.action]
            permissions.append(HasFeature(feature_code))

        # Add limit permission if action is mapped
        if self.action and self.action in self.action_limits:
            limit_key = self.action_limits[self.action]
            permissions.append(WithinUsageLimit(limit_key))

        return permissions

    def get_queryset(self):
        """Filter queryset by tenant."""
        queryset = super().get_queryset()
        tenant_id = getattr(self.request.user, "tenant_id", None)
        if tenant_id:
            return queryset.filter(tenant_id=tenant_id)
        return queryset.none()

    def perform_create(self, serializer):
        """Set tenant_id on create."""
        tenant_id = getattr(self.request.user, "tenant_id", None)
        serializer.save(tenant_id=tenant_id)


@extend_schema_view(
    list=extend_schema(
        tags=["Categories"],
        summary="List categories",
        description="Returns all categories for the authenticated user's tenant.",
    ),
    create=extend_schema(
        tags=["Categories"],
        summary="Create category",
        description="Create a new transaction category.",
    ),
    retrieve=extend_schema(
        tags=["Categories"],
        summary="Get category",
        description="Retrieve a specific category by ID.",
    ),
    update=extend_schema(
        tags=["Categories"],
        summary="Update category",
        description="Update a category.",
    ),
    partial_update=extend_schema(
        tags=["Categories"],
        summary="Partial update category",
        description="Partially update a category.",
    ),
    destroy=extend_schema(
        tags=["Categories"],
        summary="Delete category",
        description="Delete a category.",
    ),
)
class CategoryViewSet(TenantScopedViewSet):
    """ViewSet for Category management."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CreateCategorySerializer
        return CategorySerializer

    def create(self, request, *args, **kwargs):
        """Create category and return with read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return with read serializer
        read_serializer = CategorySerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    list=extend_schema(
        tags=["Accounts"],
        summary="List accounts",
        description="Returns all accounts for the authenticated user's tenant.",
    ),
    create=extend_schema(
        tags=["Accounts"],
        summary="Create account",
        description="Create a new financial account (checking, savings, credit card, etc.).",
    ),
    retrieve=extend_schema(
        tags=["Accounts"],
        summary="Get account",
        description="Retrieve a specific account by ID.",
    ),
    update=extend_schema(
        tags=["Accounts"],
        summary="Update account",
        description="Update an account.",
    ),
    partial_update=extend_schema(
        tags=["Accounts"],
        summary="Partial update account",
        description="Partially update an account.",
    ),
    destroy=extend_schema(
        tags=["Accounts"],
        summary="Delete account",
        description="Delete an account.",
    ),
)
class AccountViewSet(TenantScopedViewSet):
    """ViewSet for Account management."""

    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    # Subscription-based limits
    action_limits = {
        "create": "accounts_max",
    }

    # Premium features
    action_features = {
        "analytics": "finance.analytics",
    }

    def get_permissions(self):
        """Add account creation limit check."""
        permissions = super().get_permissions()
        # Keep legacy CanCreateAccount for backwards compatibility
        if self.action == "create":
            permissions.append(CanCreateAccount())
        return permissions

    def get_serializer_class(self):
        if self.action == "create":
            return CreateAccountSerializer
        if self.action in ["update", "partial_update"]:
            return UpdateAccountSerializer
        if self.action == "balance":
            return AccountBalanceSerializer
        return AccountSerializer

    def create(self, request, *args, **kwargs):
        """Create account and return with read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = AccountSerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        tags=["Accounts"],
        summary="Get account balance",
        description="Calculate and return the account balance from posted transactions.",
        responses={200: AccountBalanceSerializer},
    )
    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        """Get account balance.

        Calculates balance from posted transactions.
        """
        account = self.get_object()
        transactions = Transaction.objects.filter(
            account=account,
            status=Transaction.Status.POSTED,
        )

        # Calculate balance
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from decimal import Decimal

        credits = transactions.filter(
            transaction_type=Transaction.TransactionType.CREDIT
        ).aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]

        debits = transactions.filter(
            transaction_type=Transaction.TransactionType.DEBIT
        ).aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]

        balance = credits - debits

        data = {
            "account_id": account.id,
            "balance": balance,
            "total_credits": credits,
            "total_debits": debits,
            "transaction_count": transactions.count(),
            "currency_code": account.currency_code,
            "as_of_date": None,
        }
        serializer = AccountBalanceSerializer(data)
        return Response(serializer.data)

    @extend_schema(
        tags=["Accounts"],
        summary="Close account",
        description="Close an active account. Closed accounts cannot receive new transactions.",
        responses={200: AccountSerializer},
    )
    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """Close an account."""
        account = self.get_object()
        account.status = Account.Status.CLOSED
        account.save()
        serializer = AccountSerializer(account)
        return Response(serializer.data)

    @extend_schema(
        tags=["Accounts"],
        summary="Reopen account",
        description="Reopen a previously closed account.",
        responses={200: AccountSerializer},
    )
    @action(detail=True, methods=["post"])
    def reopen(self, request, pk=None):
        """Reopen a closed account."""
        account = self.get_object()
        account.status = Account.Status.ACTIVE
        account.save()
        serializer = AccountSerializer(account)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=["Transactions"],
        summary="List transactions",
        description="Returns all transactions for the authenticated user's tenant.",
        parameters=[
            OpenApiParameter(
                name="account_id",
                description="Filter by account UUID",
                required=False,
                type=str,
            ),
        ],
    ),
    create=extend_schema(
        tags=["Transactions"],
        summary="Create transaction",
        description="Create a new transaction (credit or debit).",
    ),
    retrieve=extend_schema(
        tags=["Transactions"],
        summary="Get transaction",
        description="Retrieve a specific transaction by ID.",
    ),
    update=extend_schema(
        tags=["Transactions"],
        summary="Update transaction",
        description="Update a transaction.",
    ),
    partial_update=extend_schema(
        tags=["Transactions"],
        summary="Partial update transaction",
        description="Partially update a transaction.",
    ),
    destroy=extend_schema(
        tags=["Transactions"],
        summary="Delete transaction",
        description="Delete a transaction.",
    ),
)
class TransactionViewSet(TenantScopedViewSet):
    """ViewSet for Transaction management."""

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    # Subscription-based limits
    action_limits = {
        "create": "transactions_monthly",
    }

    # Premium features
    action_features = {
        "bulk_import": "finance.bulk_import",
    }

    def get_serializer_class(self):
        if self.action == "create":
            return CreateTransactionSerializer
        if self.action == "void":
            return VoidTransactionSerializer
        return TransactionSerializer

    def get_queryset(self):
        """Filter by tenant and optionally by account."""
        queryset = super().get_queryset()
        account_id = self.request.query_params.get("account_id")
        if account_id:
            queryset = queryset.filter(account_id=account_id)
        return queryset.select_related("account", "category")

    def create(self, request, *args, **kwargs):
        """Create transaction and return with read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = TransactionSerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        tags=["Transactions"],
        summary="Post transaction",
        description="Post a pending transaction to make it final.",
        responses={200: TransactionSerializer, 400: OpenApiResponse(description="Transaction is not pending")},
    )
    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):
        """Post a pending transaction."""
        from django.utils import timezone

        transaction = self.get_object()
        if transaction.status != Transaction.Status.PENDING:
            return Response(
                {"error": _("Transaction is not pending.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        transaction.status = Transaction.Status.POSTED
        transaction.posted_at = timezone.now()
        transaction.save()
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)

    @extend_schema(
        tags=["Transactions"],
        summary="Void transaction",
        description="Void a transaction. This cannot be undone.",
        request=VoidTransactionSerializer,
        responses={200: TransactionSerializer, 400: OpenApiResponse(description="Transaction is already voided")},
    )
    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """Void a transaction."""
        transaction = self.get_object()
        if transaction.status == Transaction.Status.VOIDED:
            return Response(
                {"error": _("Transaction is already voided.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        transaction.status = Transaction.Status.VOIDED
        transaction.save()
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        tags=["Transfers"],
        summary="List transfers",
        description="Returns all transfers for the authenticated user's tenant.",
    ),
    create=extend_schema(
        tags=["Transfers"],
        summary="Create transfer",
        description="Create a transfer between two accounts. This creates linked debit and credit transactions.",
    ),
    retrieve=extend_schema(
        tags=["Transfers"],
        summary="Get transfer",
        description="Retrieve a specific transfer by ID.",
    ),
)
class TransferViewSet(TenantScopedViewSet):
    """ViewSet for Transfer management."""

    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CreateTransferSerializer
        return TransferSerializer

    def get_queryset(self):
        return super().get_queryset().select_related(
            "from_account", "to_account", "from_transaction", "to_transaction"
        )

    def create(self, request, *args, **kwargs):
        """Create transfer and return with read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = TransferSerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    list=extend_schema(
        tags=["Assets"],
        summary="List assets",
        description="Returns all assets for the authenticated user's tenant.",
    ),
    create=extend_schema(
        tags=["Assets"],
        summary="Create asset",
        description="Create a new asset (real estate, investment, vehicle, etc.).",
    ),
    retrieve=extend_schema(
        tags=["Assets"],
        summary="Get asset",
        description="Retrieve a specific asset by ID.",
    ),
    update=extend_schema(
        tags=["Assets"],
        summary="Update asset",
        description="Update an asset.",
    ),
    partial_update=extend_schema(
        tags=["Assets"],
        summary="Partial update asset",
        description="Partially update an asset.",
    ),
    destroy=extend_schema(
        tags=["Assets"],
        summary="Delete asset",
        description="Delete an asset.",
    ),
)
class AssetViewSet(TenantScopedViewSet):
    """ViewSet for Asset management."""

    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CreateAssetSerializer
        if self.action == "update_value":
            return UpdateAssetValueSerializer
        return AssetSerializer

    def create(self, request, *args, **kwargs):
        """Create asset and return with read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = AssetSerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        tags=["Assets"],
        summary="Update asset value",
        description="Update the current market value of an asset.",
        request=UpdateAssetValueSerializer,
        responses={200: AssetSerializer},
    )
    @action(detail=True, methods=["post"], url_path="update-value")
    def update_value(self, request, pk=None):
        """Update an asset's current value."""
        asset = self.get_object()
        serializer = UpdateAssetValueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        asset.current_value = serializer.validated_data["new_value"]
        asset.save()
        return Response(AssetSerializer(asset).data)


@extend_schema_view(
    list=extend_schema(
        tags=["Liabilities"],
        summary="List liabilities",
        description="Returns all liabilities for the authenticated user's tenant.",
    ),
    create=extend_schema(
        tags=["Liabilities"],
        summary="Create liability",
        description="Create a new liability (credit card, mortgage, etc.).",
    ),
    retrieve=extend_schema(
        tags=["Liabilities"],
        summary="Get liability",
        description="Retrieve a specific liability by ID.",
    ),
    update=extend_schema(
        tags=["Liabilities"],
        summary="Update liability",
        description="Update a liability.",
    ),
    partial_update=extend_schema(
        tags=["Liabilities"],
        summary="Partial update liability",
        description="Partially update a liability.",
    ),
    destroy=extend_schema(
        tags=["Liabilities"],
        summary="Delete liability",
        description="Delete a liability.",
    ),
)
class LiabilityViewSet(TenantScopedViewSet):
    """ViewSet for Liability management."""

    queryset = Liability.objects.all()
    serializer_class = LiabilitySerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CreateLiabilitySerializer
        return LiabilitySerializer

    def create(self, request, *args, **kwargs):
        """Create liability and return with read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = LiabilitySerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    list=extend_schema(
        tags=["Loans"],
        summary="List loans",
        description="Returns all loans for the authenticated user's tenant.",
    ),
    create=extend_schema(
        tags=["Loans"],
        summary="Create loan",
        description="Create a new loan with payment schedule.",
    ),
    retrieve=extend_schema(
        tags=["Loans"],
        summary="Get loan",
        description="Retrieve a specific loan by ID.",
    ),
    update=extend_schema(
        tags=["Loans"],
        summary="Update loan",
        description="Update a loan.",
    ),
    partial_update=extend_schema(
        tags=["Loans"],
        summary="Partial update loan",
        description="Partially update a loan.",
    ),
    destroy=extend_schema(
        tags=["Loans"],
        summary="Delete loan",
        description="Delete a loan.",
    ),
)
class LoanViewSet(TenantScopedViewSet):
    """ViewSet for Loan management."""

    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return CreateLoanSerializer
        if self.action == "record_payment":
            return RecordLoanPaymentSerializer
        return LoanSerializer

    def create(self, request, *args, **kwargs):
        """Create loan and return with read serializer."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        read_serializer = LoanSerializer(serializer.instance)
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        tags=["Loans"],
        summary="Record loan payment",
        description="Record a payment against a loan, reducing the principal balance.",
        request=RecordLoanPaymentSerializer,
        responses={200: LoanSerializer, 400: OpenApiResponse(description="Loan is already paid off")},
    )
    @action(detail=True, methods=["post"], url_path="record-payment")
    def record_payment(self, request, pk=None):
        """Record a loan payment."""
        loan = self.get_object()
        if loan.status == Loan.LoanStatus.PAID_OFF:
            return Response(
                {"error": _("Loan is already paid off.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RecordLoanPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Apply payment to principal
        principal = serializer.validated_data["principal_amount"]
        loan.current_balance = max(loan.current_balance - principal, 0)

        if loan.current_balance == 0:
            loan.status = Loan.LoanStatus.PAID_OFF

        loan.save()
        return Response(LoanSerializer(loan).data)


class ReportsViewSet(viewsets.ViewSet):
    """ViewSet for financial reports.

    Basic reports (net worth) are available to all users.
    Advanced reports require premium subscription.
    """

    permission_classes = [IsAuthenticated]

    # Premium features for advanced reports
    action_features = {
        "cash_flow": "reports.advanced",
        "spending_analysis": "reports.advanced",
        "income_analysis": "reports.advanced",
    }

    def get_permissions(self):
        """Add feature permissions for advanced reports."""
        permissions = super().get_permissions()

        # Add feature permission if action is mapped
        if self.action and self.action in self.action_features:
            feature_code = self.action_features[self.action]
            permissions.append(HasFeature(feature_code))

        return permissions

    @extend_schema(
        tags=["Reports"],
        summary="Calculate net worth",
        description="Calculate the total net worth for the authenticated user, including all accounts, assets, and liabilities.",
        parameters=[
            OpenApiParameter(
                name="currency",
                description="Base currency for calculation (default: USD)",
                required=False,
                type=str,
            ),
        ],
        responses={200: NetWorthSerializer, 400: OpenApiResponse(description="No tenant context")},
    )
    @action(detail=False, methods=["get"], url_path="net-worth")
    def net_worth(self, request):
        """Calculate net worth for the current tenant."""
        from decimal import Decimal
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from django.utils import timezone

        tenant_id = getattr(request.user, "tenant_id", None)
        if not tenant_id:
            return Response(
                {"error": _("No tenant context.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        currency_code = request.query_params.get("currency", "USD")

        # Calculate account balances
        accounts = Account.objects.filter(
            tenant_id=tenant_id,
            status=Account.Status.ACTIVE,
            is_included_in_net_worth=True,
        )

        account_balance = Decimal("0")
        for account in accounts:
            transactions = Transaction.objects.filter(
                account=account,
                status=Transaction.Status.POSTED,
            )
            credits = transactions.filter(
                transaction_type=Transaction.TransactionType.CREDIT
            ).aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]
            debits = transactions.filter(
                transaction_type=Transaction.TransactionType.DEBIT
            ).aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]
            account_balance += credits - debits

        # Calculate total assets
        total_assets = Asset.objects.filter(
            tenant_id=tenant_id,
            is_included_in_net_worth=True,
        ).aggregate(total=Coalesce(Sum("current_value"), Decimal("0")))["total"]

        # Calculate total liabilities
        total_liabilities = Liability.objects.filter(
            tenant_id=tenant_id,
            is_included_in_net_worth=True,
        ).aggregate(total=Coalesce(Sum("current_balance"), Decimal("0")))["total"]

        # Add active loans to liabilities
        loan_balance = Loan.objects.filter(
            tenant_id=tenant_id,
            status=Loan.LoanStatus.ACTIVE,
            is_included_in_net_worth=True,
        ).aggregate(total=Coalesce(Sum("current_balance"), Decimal("0")))["total"]
        total_liabilities += loan_balance

        net_worth = (account_balance + total_assets) - total_liabilities

        data = {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_worth": net_worth,
            "account_balances": account_balance,
            "asset_count": Asset.objects.filter(
                tenant_id=tenant_id, is_included_in_net_worth=True
            ).count(),
            "liability_count": Liability.objects.filter(
                tenant_id=tenant_id, is_included_in_net_worth=True
            ).count() + Loan.objects.filter(
                tenant_id=tenant_id,
                status=Loan.LoanStatus.ACTIVE,
                is_included_in_net_worth=True,
            ).count(),
            "account_count": accounts.count(),
            "currency_code": currency_code,
            "calculated_at": timezone.now(),
        }

        serializer = NetWorthSerializer(data)
        return Response(serializer.data)
