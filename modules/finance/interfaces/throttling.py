"""Throttle classes for the finance module.

This module provides throttle classes for rate-limiting finance API endpoints.
"""

from __future__ import annotations

from rest_framework.throttling import UserRateThrottle


class FinanceUserRateThrottle(UserRateThrottle):
    """Base throttle for finance API endpoints.

    Default rate: 200 requests per hour for regular users.
    Premium users get higher limits via PremiumFinanceRateThrottle.
    """

    scope = "finance_user"


class TransactionRateThrottle(UserRateThrottle):
    """Throttle for transaction creation.

    Rate: 100 transactions per hour.
    This protects against rapid transaction spam.
    """

    scope = "transaction_create"


class TransferRateThrottle(UserRateThrottle):
    """Throttle for transfer creation.

    Rate: 50 transfers per hour.
    Transfers involve two accounts, so rate is more conservative.
    """

    scope = "transfer_create"


class AccountCreationRateThrottle(UserRateThrottle):
    """Throttle for account creation.

    Rate: 10 accounts per hour.
    Account creation is rare, so low rate is sufficient.
    """

    scope = "account_create"


class ReportGenerationRateThrottle(UserRateThrottle):
    """Throttle for report generation.

    Rate: 30 reports per hour.
    Reports can be computationally expensive.
    """

    scope = "report_generate"


class BulkOperationRateThrottle(UserRateThrottle):
    """Throttle for bulk operations.

    Rate: 10 bulk operations per hour.
    Bulk operations are expensive and should be rate-limited aggressively.
    """

    scope = "bulk_operation"


class PremiumFinanceRateThrottle(UserRateThrottle):
    """Enhanced throttle for premium users.

    Premium users get higher rate limits.
    Rate: 1000 requests per hour.

    This throttle checks user role and applies higher limits for premium users.
    """

    scope = "premium_finance"

    def get_rate(self) -> str | None:
        """Get rate based on user role.

        Returns:
            Rate string (e.g., "1000/hour") or None.
        """
        return self.rate

    def allow_request(self, request, view) -> bool:
        """Check if request should be allowed.

        Premium and superadmin users get higher limits.
        Regular users fall back to standard FinanceUserRateThrottle.
        """
        if not request.user or not request.user.is_authenticated:
            # Anonymous users should not reach this throttle
            return True

        user_role = getattr(request.user, "role", "user")

        if user_role in ("premium", "superadmin"):
            # Apply premium rate limiting
            return super().allow_request(request, view)

        # For regular users, always allow (they use FinanceUserRateThrottle instead)
        return True


class FinanceWriteThrottle(UserRateThrottle):
    """Throttle for all write operations in finance module.

    Rate: 100 writes per hour.
    This is a catch-all throttle for POST, PUT, PATCH, DELETE.
    """

    scope = "finance_write"

    def allow_request(self, request, view) -> bool:
        """Only throttle write methods."""
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return super().allow_request(request, view)
