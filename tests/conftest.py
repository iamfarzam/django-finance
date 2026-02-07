"""Pytest configuration and shared fixtures.

This module provides fixtures used across all test modules.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Generator

import pytest
from django.test import Client
from rest_framework.test import APIClient

if TYPE_CHECKING:
    from django.contrib.auth.models import User


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
