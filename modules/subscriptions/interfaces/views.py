"""DRF views for the subscriptions module."""

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from modules.subscriptions.domain.services import PermissionService, UsageLimitService
from modules.subscriptions.infrastructure.models import Subscription, SubscriptionTier
from modules.subscriptions.interfaces.serializers import (
    SubscriptionSerializer,
    SubscriptionTierSerializer,
    UsageSummarySerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Subscriptions"],
        summary="List subscription tiers",
        description="Returns all available subscription tiers.",
    ),
    retrieve=extend_schema(
        tags=["Subscriptions"],
        summary="Get subscription details",
        description="Get the current user's subscription details.",
    ),
)
class SubscriptionViewSet(viewsets.ViewSet):
    """ViewSet for subscription management."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Subscriptions"],
        summary="List available tiers",
        description="Get all active subscription tiers available for subscription.",
        responses={200: SubscriptionTierSerializer(many=True)},
    )
    def list(self, request):
        """List all available subscription tiers."""
        tiers = SubscriptionTier.objects.filter(is_active=True).order_by("display_order")
        serializer = SubscriptionTierSerializer(tiers, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Subscriptions"],
        summary="Get current subscription",
        description="Get the authenticated user's current subscription.",
        responses={200: SubscriptionSerializer},
    )
    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        """Get the current user's subscription."""
        try:
            subscription = Subscription.objects.select_related("tier").get(
                user=request.user
            )
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data)
        except Subscription.DoesNotExist:
            # Return default free tier info
            return Response({
                "tier": "free",
                "status": "active",
                "is_premium": False,
                "message": _("No subscription found. Using free tier."),
            })

    @extend_schema(
        tags=["Subscriptions"],
        summary="Get usage summary",
        description="Get the current user's usage summary and remaining limits.",
        responses={200: UsageSummarySerializer},
    )
    @action(detail=False, methods=["get"], url_path="usage")
    def usage(self, request):
        """Get the current user's usage summary."""
        context = PermissionService.get_user_context(request.user)

        # Get current usage counts
        from modules.subscriptions.domain.enums import UsageType

        usage_data = {
            "tier": context.tier_code,
            "is_premium": context.is_premium,
            "limits": context.limits,
            "features": context.features,
            "usage": {},
        }

        # Add current usage for each limit
        for limit_key, limit_value in context.limits.items():
            # Map limit keys to usage types
            usage_type_map = {
                "accounts_max": UsageType.ACCOUNTS.value,
                "transactions_monthly": UsageType.TRANSACTIONS_MONTHLY.value,
                "contacts_max": UsageType.CONTACTS.value,
                "expense_groups_max": UsageType.EXPENSE_GROUPS.value,
                "api_calls_daily": UsageType.API_CALLS_DAILY.value,
            }
            usage_type = usage_type_map.get(limit_key)
            if usage_type:
                current = UsageLimitService.get_current_usage(request.user, usage_type)
                usage_data["usage"][limit_key] = {
                    "current": current,
                    "limit": limit_value if limit_value else "unlimited",
                    "remaining": (limit_value - current) if limit_value else "unlimited",
                }

        serializer = UsageSummarySerializer(usage_data)
        return Response(serializer.data)

    @extend_schema(
        tags=["Subscriptions"],
        summary="Webhook endpoint (stub)",
        description="Stripe webhook endpoint for subscription events. Not implemented.",
        responses={200: None},
    )
    @action(detail=False, methods=["post"], url_path="webhook")
    def webhook(self, request):
        """Stripe webhook endpoint (stub for future implementation)."""
        # This is a stub for future Stripe integration
        # Events to handle:
        # - customer.subscription.created
        # - customer.subscription.updated
        # - customer.subscription.deleted
        # - invoice.paid
        # - invoice.payment_failed
        return Response({"status": "webhook received"}, status=status.HTTP_200_OK)
