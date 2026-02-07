"""Integration tests for the Finance API endpoints.

These tests verify the complete request/response flow for finance operations,
including authentication, serialization, database operations, and response formatting.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from rest_framework import status

if TYPE_CHECKING:
    from rest_framework.test import APIClient

    from modules.accounts.infrastructure.models import User


pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db) -> "User":
    """Create and return a test user."""
    from modules.accounts.infrastructure.models import User

    user = User.objects.create_user(
        email="testuser@example.com",
        password="TestPass123!",
        first_name="Test",
        last_name="User",
        role=User.Role.USER,
        status=User.Status.ACTIVE,
        is_email_verified=True,
    )
    return user


@pytest.fixture
def premium_user(db) -> "User":
    """Create and return a premium test user."""
    from modules.accounts.infrastructure.models import User

    user = User.objects.create_user(
        email="premium@example.com",
        password="TestPass123!",
        first_name="Premium",
        last_name="User",
        role=User.Role.PREMIUM,
        status=User.Status.ACTIVE,
        is_email_verified=True,
    )
    return user


@pytest.fixture
def authenticated_client(api_client: "APIClient", user: "User") -> "APIClient":
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def premium_client(api_client: "APIClient", premium_user: "User") -> "APIClient":
    """Return an authenticated API client for premium user."""
    api_client.force_authenticate(user=premium_user)
    return api_client


class TestAccountAPI:
    """Tests for the Account API endpoints."""

    def test_create_account(self, authenticated_client: "APIClient", user: "User"):
        """Test creating a new account."""
        url = reverse("api-v1:finance:account-list")
        data = {
            "name": "Checking Account",
            "account_type": "checking",
            "currency_code": "USD",
            "institution": "Test Bank",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Checking Account"
        assert response.data["account_type"] == "checking"
        assert response.data["currency_code"] == "USD"
        assert "id" in response.data

    def test_create_account_invalid_currency(
        self, authenticated_client: "APIClient", user: "User"
    ):
        """Test creating account with invalid currency fails."""
        url = reverse("api-v1:finance:account-list")
        data = {
            "name": "Test Account",
            "account_type": "checking",
            "currency_code": "XYZ",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Error is wrapped in custom error format
        assert "error" in response.data
        assert "currency_code" in str(response.data["error"]["message"])

    def test_list_accounts(self, authenticated_client: "APIClient", user: "User"):
        """Test listing accounts for current tenant."""
        from modules.finance.infrastructure.models import Account

        # Create accounts
        Account.objects.create(
            tenant_id=user.tenant_id,
            name="Account 1",
            account_type="checking",
            currency_code="USD",
        )
        Account.objects.create(
            tenant_id=user.tenant_id,
            name="Account 2",
            account_type="savings",
            currency_code="USD",
        )

        url = reverse("api-v1:finance:account-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_accounts_tenant_isolation(
        self, authenticated_client: "APIClient", user: "User"
    ):
        """Test that accounts from other tenants are not visible."""
        from modules.finance.infrastructure.models import Account

        # Create account for current user
        Account.objects.create(
            tenant_id=user.tenant_id,
            name="My Account",
            account_type="checking",
            currency_code="USD",
        )
        # Create account for different tenant
        other_tenant = uuid.uuid4()
        Account.objects.create(
            tenant_id=other_tenant,
            name="Other Account",
            account_type="checking",
            currency_code="USD",
        )

        url = reverse("api-v1:finance:account-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["name"] == "My Account"

    def test_get_account_balance(self, authenticated_client: "APIClient", user: "User"):
        """Test getting account balance."""
        from modules.finance.infrastructure.models import Account, Transaction

        account = Account.objects.create(
            tenant_id=user.tenant_id,
            name="Test Account",
            account_type="checking",
            currency_code="USD",
        )
        # Add transactions
        Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="credit",
            amount=Decimal("1000.00"),
            currency_code="USD",
            status="posted",
            transaction_date=date.today(),
        )
        Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="debit",
            amount=Decimal("250.00"),
            currency_code="USD",
            status="posted",
            transaction_date=date.today(),
        )

        url = reverse("api-v1:finance:account-balance", kwargs={"pk": account.id})
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["balance"]) == Decimal("750.00")
        assert Decimal(response.data["total_credits"]) == Decimal("1000.00")
        assert Decimal(response.data["total_debits"]) == Decimal("250.00")

    def test_close_account(self, authenticated_client: "APIClient", user: "User"):
        """Test closing an account."""
        from modules.finance.infrastructure.models import Account

        account = Account.objects.create(
            tenant_id=user.tenant_id,
            name="Test Account",
            account_type="checking",
            currency_code="USD",
        )

        url = reverse("api-v1:finance:account-close", kwargs={"pk": account.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "closed"

    def test_unauthenticated_access_denied(self, api_client: "APIClient"):
        """Test that unauthenticated requests are denied."""
        url = reverse("api-v1:finance:account-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTransactionAPI:
    """Tests for the Transaction API endpoints."""

    @pytest.fixture
    def account(self, user: "User"):
        """Create and return a test account."""
        from modules.finance.infrastructure.models import Account

        return Account.objects.create(
            tenant_id=user.tenant_id,
            name="Test Account",
            account_type="checking",
            currency_code="USD",
        )

    def test_create_transaction(
        self, authenticated_client: "APIClient", user: "User", account
    ):
        """Test creating a transaction."""
        url = reverse("api-v1:finance:transaction-list")
        data = {
            "account_id": str(account.id),
            "transaction_type": "credit",
            "amount": "500.00",
            "currency_code": "USD",
            "description": "Salary deposit",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data["amount"]) == Decimal("500.00")
        assert response.data["transaction_type"] == "credit"

    def test_create_transaction_negative_amount_fails(
        self, authenticated_client: "APIClient", user: "User", account
    ):
        """Test that negative amounts are rejected."""
        url = reverse("api-v1:finance:transaction-list")
        data = {
            "account_id": str(account.id),
            "transaction_type": "credit",
            "amount": "-100.00",
            "currency_code": "USD",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_transactions(
        self, authenticated_client: "APIClient", user: "User", account
    ):
        """Test listing transactions."""
        from modules.finance.infrastructure.models import Transaction

        Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="credit",
            amount=Decimal("100.00"),
            currency_code="USD",
            status="posted",
            transaction_date=date.today(),
        )
        Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="debit",
            amount=Decimal("50.00"),
            currency_code="USD",
            status="posted",
            transaction_date=date.today(),
        )

        url = reverse("api-v1:finance:transaction-list")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_filter_transactions_by_account(
        self, authenticated_client: "APIClient", user: "User", account
    ):
        """Test filtering transactions by account."""
        from modules.finance.infrastructure.models import Account, Transaction

        other_account = Account.objects.create(
            tenant_id=user.tenant_id,
            name="Other Account",
            account_type="savings",
            currency_code="USD",
        )

        Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="credit",
            amount=Decimal("100.00"),
            currency_code="USD",
            transaction_date=date.today(),
        )
        Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=other_account,
            transaction_type="credit",
            amount=Decimal("200.00"),
            currency_code="USD",
            transaction_date=date.today(),
        )

        url = f"{reverse('api-v1:finance:transaction-list')}?account_id={account.id}"
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_post_transaction(
        self, authenticated_client: "APIClient", user: "User", account
    ):
        """Test posting a pending transaction."""
        from modules.finance.infrastructure.models import Transaction

        transaction = Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="credit",
            amount=Decimal("100.00"),
            currency_code="USD",
            status="pending",
            transaction_date=date.today(),
        )

        url = reverse("api-v1:finance:transaction-post", kwargs={"pk": transaction.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "posted"
        assert response.data["posted_at"] is not None

    def test_void_transaction(
        self, authenticated_client: "APIClient", user: "User", account
    ):
        """Test voiding a transaction."""
        from modules.finance.infrastructure.models import Transaction

        transaction = Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="credit",
            amount=Decimal("100.00"),
            currency_code="USD",
            status="posted",
            transaction_date=date.today(),
        )

        url = reverse("api-v1:finance:transaction-void", kwargs={"pk": transaction.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "voided"


class TestTransferAPI:
    """Tests for the Transfer API endpoints."""

    @pytest.fixture
    def accounts(self, user: "User"):
        """Create and return test accounts."""
        from modules.finance.infrastructure.models import Account

        from_account = Account.objects.create(
            tenant_id=user.tenant_id,
            name="From Account",
            account_type="checking",
            currency_code="USD",
        )
        to_account = Account.objects.create(
            tenant_id=user.tenant_id,
            name="To Account",
            account_type="savings",
            currency_code="USD",
        )
        return from_account, to_account

    def test_create_transfer(
        self, authenticated_client: "APIClient", user: "User", accounts
    ):
        """Test creating a transfer."""
        from_account, to_account = accounts

        url = reverse("api-v1:finance:transfer-list")
        data = {
            "from_account_id": str(from_account.id),
            "to_account_id": str(to_account.id),
            "amount": "250.00",
            "currency_code": "USD",
            "description": "Savings transfer",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(response.data["amount"]) == Decimal("250.00")

    def test_create_transfer_same_account_fails(
        self, authenticated_client: "APIClient", user: "User", accounts
    ):
        """Test that transfer to same account fails."""
        from_account, _ = accounts

        url = reverse("api-v1:finance:transfer-list")
        data = {
            "from_account_id": str(from_account.id),
            "to_account_id": str(from_account.id),
            "amount": "100.00",
            "currency_code": "USD",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAssetAPI:
    """Tests for the Asset API endpoints."""

    def test_create_asset(self, authenticated_client: "APIClient", user: "User"):
        """Test creating an asset."""
        url = reverse("api-v1:finance:asset-list")
        data = {
            "name": "Investment Portfolio",
            "asset_type": "investment",
            "current_value": "50000.00",
            "currency_code": "USD",
            "purchase_price": "40000.00",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Investment Portfolio"
        assert Decimal(response.data["current_value"]) == Decimal("50000.00")

    def test_update_asset_value(self, authenticated_client: "APIClient", user: "User"):
        """Test updating an asset's value."""
        from modules.finance.infrastructure.models import Asset

        asset = Asset.objects.create(
            tenant_id=user.tenant_id,
            name="Stock Portfolio",
            asset_type="investment",
            current_value=Decimal("10000.00"),
            currency_code="USD",
        )

        url = reverse("api-v1:finance:asset-update-value", kwargs={"pk": asset.id})
        response = authenticated_client.post(
            url, {"new_value": "12000.00"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["current_value"]) == Decimal("12000.00")


class TestLiabilityAPI:
    """Tests for the Liability API endpoints."""

    def test_create_liability(self, authenticated_client: "APIClient", user: "User"):
        """Test creating a liability."""
        url = reverse("api-v1:finance:liability-list")
        data = {
            "name": "Credit Card",
            "liability_type": "credit_card",
            "current_balance": "5000.00",
            "currency_code": "USD",
            "interest_rate": "18.99",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Credit Card"


class TestLoanAPI:
    """Tests for the Loan API endpoints."""

    def test_create_loan(self, authenticated_client: "APIClient", user: "User"):
        """Test creating a loan."""
        url = reverse("api-v1:finance:loan-list")
        data = {
            "name": "Auto Loan",
            "liability_type": "auto_loan",
            "principal": "25000.00",
            "currency_code": "USD",
            "interest_rate": "5.50",
            "payment_amount": "500.00",
            "payment_frequency": "monthly",
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Auto Loan"
        assert Decimal(response.data["original_principal"]) == Decimal("25000.00")

    def test_record_loan_payment(
        self, authenticated_client: "APIClient", user: "User"
    ):
        """Test recording a loan payment."""
        from modules.finance.infrastructure.models import Loan

        loan = Loan.objects.create(
            tenant_id=user.tenant_id,
            name="Personal Loan",
            liability_type="personal_loan",
            original_principal=Decimal("10000.00"),
            current_balance=Decimal("10000.00"),
            currency_code="USD",
            interest_rate=Decimal("8.00"),
            payment_amount=Decimal("300.00"),
            payment_frequency="monthly",
        )

        url = reverse("api-v1:finance:loan-record-payment", kwargs={"pk": loan.id})
        response = authenticated_client.post(
            url, {"principal_amount": "500.00"}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert Decimal(response.data["current_balance"]) == Decimal("9500.00")


class TestReportsAPI:
    """Tests for the Reports API endpoints."""

    def test_net_worth_calculation(
        self, authenticated_client: "APIClient", user: "User"
    ):
        """Test net worth calculation."""
        from modules.finance.infrastructure.models import Account, Asset, Liability, Transaction

        # Create account with balance
        account = Account.objects.create(
            tenant_id=user.tenant_id,
            name="Checking",
            account_type="checking",
            currency_code="USD",
            is_included_in_net_worth=True,
        )
        Transaction.objects.create(
            tenant_id=user.tenant_id,
            account=account,
            transaction_type="credit",
            amount=Decimal("5000.00"),
            currency_code="USD",
            status="posted",
            transaction_date=date.today(),
        )

        # Create asset
        Asset.objects.create(
            tenant_id=user.tenant_id,
            name="Investment",
            asset_type="investment",
            current_value=Decimal("20000.00"),
            currency_code="USD",
            is_included_in_net_worth=True,
        )

        # Create liability
        Liability.objects.create(
            tenant_id=user.tenant_id,
            name="Credit Card",
            liability_type="credit_card",
            current_balance=Decimal("3000.00"),
            currency_code="USD",
            is_included_in_net_worth=True,
        )

        url = reverse("api-v1:finance:report-net-worth")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Net worth = Account balance (5000) + Assets (20000) - Liabilities (3000) = 22000
        assert Decimal(response.data["net_worth"]) == Decimal("22000.00")


class TestCategoryAPI:
    """Tests for the Category API endpoints."""

    def test_create_category(self, authenticated_client: "APIClient", user: "User"):
        """Test creating a category."""
        url = reverse("api-v1:finance:category-list")
        data = {
            "name": "Groceries",
            "is_income": False,
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "Groceries"
        assert response.data["is_income"] is False

    def test_create_subcategory(self, authenticated_client: "APIClient", user: "User"):
        """Test creating a subcategory."""
        from modules.finance.infrastructure.models import Category

        parent = Category.objects.create(
            tenant_id=user.tenant_id,
            name="Food",
            is_income=False,
        )

        url = reverse("api-v1:finance:category-list")
        data = {
            "name": "Restaurants",
            "parent_id": str(parent.id),
            "is_income": False,
        }
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["parent"] == str(parent.id)
