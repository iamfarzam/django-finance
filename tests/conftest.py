"""Pytest configuration and shared fixtures.

This module provides fixtures used across all test modules.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Generator

import pytest
from django.test import Client
from rest_framework.test import APIClient

if TYPE_CHECKING:
    from modules.accounts.infrastructure.models import User


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated API client.

    Returns:
        DRF API test client.
    """
    return APIClient()


@pytest.fixture
def client() -> Client:
    """Return a Django test client.

    Returns:
        Django test client.
    """
    return Client()


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Return a test tenant ID.

    Returns:
        UUID for a test tenant.
    """
    return uuid.uuid4()


@pytest.fixture
def correlation_id() -> str:
    """Return a test correlation ID.

    Returns:
        String correlation ID.
    """
    return str(uuid.uuid4())


@pytest.fixture
def mock_tenant_context(
    tenant_id: uuid.UUID,
) -> Generator[uuid.UUID, None, None]:
    """Set up mock tenant context for tests.

    Args:
        tenant_id: The tenant ID to use.

    Yields:
        The tenant ID being used.
    """
    from shared.middleware import tenant_id_var

    token = tenant_id_var.set(tenant_id)
    try:
        yield tenant_id
    finally:
        tenant_id_var.reset(token)


@pytest.fixture
def mock_correlation_context(
    correlation_id: str,
) -> Generator[str, None, None]:
    """Set up mock correlation ID context for tests.

    Args:
        correlation_id: The correlation ID to use.

    Yields:
        The correlation ID being used.
    """
    from shared.middleware import correlation_id_var

    token = correlation_id_var.set(correlation_id)
    try:
        yield correlation_id
    finally:
        correlation_id_var.reset(token)


# Mark for database access
@pytest.fixture
def db_access(db: Any) -> None:
    """Mark test as needing database access.

    This is an alias for the built-in db fixture that makes
    the intent clearer.
    """
    pass


# Mark for transactional tests
@pytest.fixture
def transactional_db_access(transactional_db: Any) -> None:
    """Mark test as needing transactional database access.

    This is an alias for the built-in transactional_db fixture.
    """
    pass


# User fixtures for integration tests
@pytest.fixture
def user(db) -> "User":
    """Create and return a standard test user.

    Returns:
        A verified, active user with USER role.
    """
    from modules.accounts.infrastructure.models import User

    user = User.objects.create_user(
        email="testuser@example.com",
        password="TestPass123!@#",
        first_name="Test",
        last_name="User",
        role=User.Role.USER,
        status=User.Status.ACTIVE,
        is_email_verified=True,
    )
    return user


@pytest.fixture
def premium_user(db) -> "User":
    """Create and return a premium test user.

    Returns:
        A verified, active user with PREMIUM role.
    """
    from modules.accounts.infrastructure.models import User

    user = User.objects.create_user(
        email="premium@example.com",
        password="TestPass123!@#",
        first_name="Premium",
        last_name="User",
        role=User.Role.PREMIUM,
        status=User.Status.ACTIVE,
        is_email_verified=True,
    )
    return user


@pytest.fixture
def superadmin_user(db) -> "User":
    """Create and return a superadmin test user.

    Returns:
        A verified, active superadmin user.
    """
    from modules.accounts.infrastructure.models import User

    user = User.objects.create_superuser(
        email="admin@example.com",
        password="AdminPass123!@#",
    )
    return user


@pytest.fixture
def authenticated_client(api_client: APIClient, user: "User") -> APIClient:
    """Return an authenticated API client for standard user.

    Args:
        api_client: The base API client.
        user: The user to authenticate.

    Returns:
        Authenticated API client.
    """
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def premium_client(api_client: APIClient, premium_user: "User") -> APIClient:
    """Return an authenticated API client for premium user.

    Args:
        api_client: The base API client.
        premium_user: The premium user to authenticate.

    Returns:
        Authenticated API client.
    """
    api_client.force_authenticate(user=premium_user)
    return api_client


@pytest.fixture
def admin_client(api_client: APIClient, superadmin_user: "User") -> APIClient:
    """Return an authenticated API client for superadmin.

    Args:
        api_client: The base API client.
        superadmin_user: The superadmin user to authenticate.

    Returns:
        Authenticated API client.
    """
    api_client.force_authenticate(user=superadmin_user)
    return api_client


# Finance fixtures
@pytest.fixture
def account(user: "User"):
    """Create and return a test account.

    Args:
        user: The user who owns the account.

    Returns:
        A checking account for the user.
    """
    from modules.finance.infrastructure.models import Account

    return Account.objects.create(
        tenant_id=user.tenant_id,
        name="Test Checking Account",
        account_type="checking",
        currency_code="USD",
        institution="Test Bank",
    )


@pytest.fixture
def category(user: "User"):
    """Create and return a test category.

    Args:
        user: The user who owns the category.

    Returns:
        An expense category for the user.
    """
    from modules.finance.infrastructure.models import Category

    return Category.objects.create(
        tenant_id=user.tenant_id,
        name="Groceries",
        is_income=False,
    )


@pytest.fixture
def transaction(user: "User", account):
    """Create and return a test transaction.

    Args:
        user: The user who owns the transaction.
        account: The account for the transaction.

    Returns:
        A posted credit transaction.
    """
    from modules.finance.infrastructure.models import Transaction

    return Transaction.objects.create(
        tenant_id=user.tenant_id,
        account=account,
        transaction_type="credit",
        amount=Decimal("1000.00"),
        currency_code="USD",
        status="posted",
        description="Test deposit",
    )
