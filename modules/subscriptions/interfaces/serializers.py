"""DRF serializers for the subscriptions module."""

from rest_framework import serializers

from modules.subscriptions.infrastructure.models import Subscription, SubscriptionTier


class SubscriptionTierSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionTier model."""

    class Meta:
        model = SubscriptionTier
        fields = [
            "id",
            "code",
            "name",
            "description",
            "limits",
            "features",
            "price_monthly",
            "price_yearly",
            "display_order",
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""

    tier_code = serializers.CharField(source="tier.code", read_only=True)
    tier_name = serializers.CharField(source="tier.name", read_only=True)
    is_active = serializers.SerializerMethodField()
    is_premium = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    limits = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "tier_code",
            "tier_name",
            "status",
            "billing_cycle",
            "current_period_start",
            "current_period_end",
            "trial_start",
            "trial_end",
            "canceled_at",
            "cancel_at_period_end",
            "is_active",
            "is_premium",
            "days_until_expiry",
            "features",
            "limits",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_is_active(self, obj):
        """Check if subscription is active."""
        return obj.is_active()

    def get_is_premium(self, obj):
        """Check if subscription is premium."""
        return obj.is_premium()

    def get_days_until_expiry(self, obj):
        """Get days until subscription expires."""
        return obj.days_until_expiry()

    def get_features(self, obj):
        """Get list of features for this subscription."""
        return obj.tier.features or []

    def get_limits(self, obj):
        """Get limits for this subscription."""
        return obj.tier.limits or {}


class UsageItemSerializer(serializers.Serializer):
    """Serializer for a single usage item."""

    current = serializers.IntegerField()
    limit = serializers.CharField()  # Can be int or "unlimited"
    remaining = serializers.CharField()  # Can be int or "unlimited"


class UsageSummarySerializer(serializers.Serializer):
    """Serializer for usage summary response."""

    tier = serializers.CharField()
    is_premium = serializers.BooleanField()
    limits = serializers.DictField()
    features = serializers.ListField(child=serializers.CharField())
    usage = serializers.DictField(child=UsageItemSerializer())
