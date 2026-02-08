"""DRF serializers for the finance module."""

from decimal import Decimal
from typing import Any, ClassVar

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from modules.finance.domain.value_objects import Currency
from shared.serializers import FieldPermissionMixin
from modules.finance.infrastructure.models import (
    Account,
    Asset,
    Category,
    Liability,
    Loan,
    Transaction,
    Transfer,
)


class CurrencyField(serializers.CharField):
    """Custom field for currency codes with validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 3)
        kwargs.setdefault("min_length", 3)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        value = super().to_internal_value(data).upper()
        if not Currency.is_supported(value):
            raise serializers.ValidationError(_("Unsupported currency: %(currency)s") % {"currency": value})
        return value


class MoneyField(serializers.DecimalField):
    """Custom field for monetary amounts with validation."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_digits", 19)
        kwargs.setdefault("decimal_places", 4)
        kwargs.setdefault("min_value", Decimal("0"))
        super().__init__(**kwargs)


# =============================================================================
# Category Serializers
# =============================================================================


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    parent = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "parent",
            "icon",
            "color",
            "is_system",
            "is_income",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_parent(self, obj):
        """Return parent ID as string."""
        if obj.parent_id:
            return str(obj.parent_id)
        return None


class CreateCategorySerializer(serializers.Serializer):
    """Serializer for creating a category."""

    name = serializers.CharField(max_length=100)
    parent_id = serializers.UUIDField(required=False, allow_null=True)
    icon = serializers.CharField(max_length=50, required=False, allow_null=True)
    color = serializers.CharField(max_length=7, required=False, allow_null=True)
    is_income = serializers.BooleanField(default=False)

    def create(self, validated_data):
        """Create a new category."""
        parent_id = validated_data.pop("parent_id", None)
        if parent_id:
            validated_data["parent_id"] = parent_id
        return Category.objects.create(**validated_data)


# =============================================================================
# Account Serializers
# =============================================================================


class AccountSerializer(FieldPermissionMixin, serializers.ModelSerializer):
    """Serializer for Account model.

    Includes field-level permissions for premium features.
    """

    # Premium field permissions
    premium_fields: ClassVar[dict[str, str]] = {
        "account_number_masked": "finance.view_sensitive",
        "notes": "finance.view_notes",
    }

    # Masking for non-premium users
    masked_fields: ClassVar[dict[str, Any]] = {
        "account_number_masked": "****",
    }

    balance = serializers.DecimalField(
        max_digits=19, decimal_places=4, read_only=True, required=False
    )
    formatted_balance = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "account_type",
            "currency_code",
            "status",
            "institution",
            "account_number_masked",
            "notes",
            "is_included_in_net_worth",
            "display_order",
            "balance",
            "formatted_balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]


class CreateAccountSerializer(serializers.Serializer):
    """Serializer for creating an account."""

    name = serializers.CharField(max_length=100)
    account_type = serializers.ChoiceField(choices=Account.AccountType.choices)
    currency_code = CurrencyField()
    institution = serializers.CharField(max_length=100, required=False, allow_null=True)
    account_number_masked = serializers.CharField(max_length=50, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    initial_balance = MoneyField(required=False, allow_null=True)

    def create(self, validated_data):
        """Create a new account."""
        validated_data.pop("initial_balance", None)  # Handle separately if needed
        return Account.objects.create(**validated_data)


class UpdateAccountSerializer(serializers.Serializer):
    """Serializer for updating an account."""

    name = serializers.CharField(max_length=100, required=False)
    institution = serializers.CharField(max_length=100, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    is_included_in_net_worth = serializers.BooleanField(required=False)


class AccountBalanceSerializer(serializers.Serializer):
    """Serializer for account balance response."""

    account_id = serializers.UUIDField()
    balance = serializers.DecimalField(max_digits=19, decimal_places=4)
    total_credits = serializers.DecimalField(max_digits=19, decimal_places=4)
    total_debits = serializers.DecimalField(max_digits=19, decimal_places=4)
    transaction_count = serializers.IntegerField()
    currency_code = serializers.CharField()
    as_of_date = serializers.DateField(allow_null=True)


# =============================================================================
# Transaction Serializers
# =============================================================================


class TransactionSerializer(FieldPermissionMixin, serializers.ModelSerializer):
    """Serializer for Transaction model.

    Includes field-level permissions for premium features.
    """

    # Premium field permissions
    premium_fields: ClassVar[dict[str, str]] = {
        "reference_number": "finance.view_sensitive",
        "notes": "finance.view_notes",
    }

    # Masking for non-premium users
    masked_fields: ClassVar[dict[str, Any]] = {
        "reference_number": "****",
    }

    category_name = serializers.CharField(source="category.name", read_only=True)
    signed_amount = serializers.SerializerMethodField()
    formatted_amount = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "account",
            "transaction_type",
            "amount",
            "currency_code",
            "status",
            "transaction_date",
            "posted_at",
            "description",
            "category",
            "category_name",
            "reference_number",
            "notes",
            "adjustment_for",
            "signed_amount",
            "formatted_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "posted_at", "adjustment_for", "created_at", "updated_at"]

    def get_signed_amount(self, obj):
        """Calculate signed amount for balance display."""
        if obj.transaction_type == Transaction.TransactionType.CREDIT:
            return obj.amount
        return -obj.amount

    def get_formatted_amount(self, obj):
        """Format amount with currency symbol."""
        currency = Currency.get(obj.currency_code)
        sign = "+" if obj.transaction_type == Transaction.TransactionType.CREDIT else "-"
        return f"{sign}{currency.symbol}{obj.amount}"


class CreateTransactionSerializer(serializers.Serializer):
    """Serializer for creating a transaction."""

    account_id = serializers.UUIDField()
    transaction_type = serializers.ChoiceField(choices=Transaction.TransactionType.choices)
    amount = MoneyField()
    currency_code = CurrencyField()
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    transaction_date = serializers.DateField(required=False)
    category_id = serializers.UUIDField(required=False, allow_null=True)
    reference_number = serializers.CharField(max_length=100, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(max_length=255, required=False, allow_null=True)
    auto_post = serializers.BooleanField(default=True)

    def create(self, validated_data):
        """Create a new transaction."""
        from datetime import date

        validated_data.pop("idempotency_key", None)
        validated_data.pop("auto_post", None)
        validated_data["account_id"] = validated_data.pop("account_id")
        if "transaction_date" not in validated_data:
            validated_data["transaction_date"] = date.today()
        return Transaction.objects.create(**validated_data)


class VoidTransactionSerializer(serializers.Serializer):
    """Serializer for voiding a transaction."""

    reason = serializers.CharField(required=False, allow_null=True)


# =============================================================================
# Transfer Serializers
# =============================================================================


class TransferSerializer(serializers.ModelSerializer):
    """Serializer for Transfer model."""

    class Meta:
        model = Transfer
        fields = [
            "id",
            "from_account",
            "to_account",
            "amount",
            "currency_code",
            "from_transaction",
            "to_transaction",
            "transfer_date",
            "description",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "from_transaction", "to_transaction", "created_at"]


class CreateTransferSerializer(serializers.Serializer):
    """Serializer for creating a transfer."""

    from_account_id = serializers.UUIDField()
    to_account_id = serializers.UUIDField()
    amount = MoneyField()
    currency_code = CurrencyField()
    transfer_date = serializers.DateField(required=False)
    description = serializers.CharField(max_length=500, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_null=True)
    idempotency_key = serializers.CharField(max_length=255, required=False, allow_null=True)

    def validate(self, data):
        """Validate that accounts are different."""
        if data["from_account_id"] == data["to_account_id"]:
            raise serializers.ValidationError(
                {"to_account_id": _("Cannot transfer to the same account.")}
            )
        return data

    def create(self, validated_data):
        """Create a new transfer."""
        from datetime import date

        validated_data.pop("idempotency_key", None)
        if "transfer_date" not in validated_data:
            validated_data["transfer_date"] = date.today()
        return Transfer.objects.create(**validated_data)


# =============================================================================
# Asset Serializers
# =============================================================================


class AssetSerializer(serializers.ModelSerializer):
    """Serializer for Asset model."""

    gain_loss = serializers.SerializerMethodField()
    formatted_value = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            "id",
            "name",
            "asset_type",
            "current_value",
            "currency_code",
            "purchase_date",
            "purchase_price",
            "description",
            "notes",
            "is_included_in_net_worth",
            "gain_loss",
            "formatted_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_gain_loss(self, obj):
        """Calculate gain/loss if purchase price is known."""
        if obj.purchase_price is None:
            return None
        return obj.current_value - obj.purchase_price

    def get_formatted_value(self, obj):
        """Format current value with currency symbol."""
        currency = Currency.get(obj.currency_code)
        return f"{currency.symbol}{obj.current_value}"


class CreateAssetSerializer(serializers.Serializer):
    """Serializer for creating an asset."""

    name = serializers.CharField(max_length=200)
    asset_type = serializers.ChoiceField(choices=Asset.AssetType.choices)
    current_value = MoneyField()
    currency_code = CurrencyField()
    purchase_date = serializers.DateField(required=False, allow_null=True)
    purchase_price = MoneyField(required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        """Create a new asset."""
        return Asset.objects.create(**validated_data)


class UpdateAssetValueSerializer(serializers.Serializer):
    """Serializer for updating an asset's value."""

    new_value = MoneyField()


# =============================================================================
# Liability Serializers
# =============================================================================


class LiabilitySerializer(FieldPermissionMixin, serializers.ModelSerializer):
    """Serializer for Liability model.

    Includes field-level permissions for premium features.
    """

    # Premium field permissions
    premium_fields: ClassVar[dict[str, str]] = {
        "interest_rate": "finance.view_rates",
        "account_number_masked": "finance.view_sensitive",
        "notes": "finance.view_notes",
    }

    # Masking for non-premium users
    masked_fields: ClassVar[dict[str, Any]] = {
        "account_number_masked": "****",
    }

    formatted_balance = serializers.SerializerMethodField()

    class Meta:
        model = Liability
        fields = [
            "id",
            "name",
            "liability_type",
            "current_balance",
            "currency_code",
            "interest_rate",
            "minimum_payment",
            "due_day",
            "creditor",
            "account_number_masked",
            "notes",
            "is_included_in_net_worth",
            "formatted_balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_formatted_balance(self, obj):
        """Format balance with currency symbol."""
        currency = Currency.get(obj.currency_code)
        return f"{currency.symbol}{obj.current_balance}"


class CreateLiabilitySerializer(serializers.Serializer):
    """Serializer for creating a liability."""

    name = serializers.CharField(max_length=200)
    liability_type = serializers.ChoiceField(choices=Liability.LiabilityType.choices)
    current_balance = MoneyField()
    currency_code = CurrencyField()
    interest_rate = serializers.DecimalField(
        max_digits=6, decimal_places=4, required=False, allow_null=True
    )
    minimum_payment = MoneyField(required=False, allow_null=True)
    due_day = serializers.IntegerField(min_value=1, max_value=31, required=False, allow_null=True)
    creditor = serializers.CharField(max_length=100, required=False, allow_null=True)
    account_number_masked = serializers.CharField(max_length=50, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        """Create a new liability."""
        return Liability.objects.create(**validated_data)


# =============================================================================
# Loan Serializers
# =============================================================================


class LoanSerializer(FieldPermissionMixin, serializers.ModelSerializer):
    """Serializer for Loan model.

    Includes field-level permissions for premium features.
    """

    # Premium field permissions
    premium_fields: ClassVar[dict[str, str]] = {
        "interest_rate": "finance.view_rates",
        "account_number_masked": "finance.view_sensitive",
        "notes": "finance.view_notes",
    }

    # Masking for non-premium users
    masked_fields: ClassVar[dict[str, Any]] = {
        "account_number_masked": "****",
    }

    principal_paid = serializers.SerializerMethodField()
    principal_paid_percentage = serializers.SerializerMethodField()
    formatted_balance = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id",
            "name",
            "liability_type",
            "original_principal",
            "current_balance",
            "currency_code",
            "interest_rate",
            "payment_amount",
            "payment_frequency",
            "status",
            "start_date",
            "expected_payoff_date",
            "next_payment_date",
            "lender",
            "account_number_masked",
            "notes",
            "linked_account",
            "is_included_in_net_worth",
            "principal_paid",
            "principal_paid_percentage",
            "formatted_balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "created_at", "updated_at"]

    def get_principal_paid(self, obj):
        """Calculate principal paid so far."""
        return obj.original_principal - obj.current_balance

    def get_principal_paid_percentage(self, obj):
        """Calculate percentage of principal paid."""
        if obj.original_principal == 0:
            return Decimal("100")
        paid = obj.original_principal - obj.current_balance
        return (paid / obj.original_principal) * Decimal("100")

    def get_formatted_balance(self, obj):
        """Format balance with currency symbol."""
        currency = Currency.get(obj.currency_code)
        return f"{currency.symbol}{obj.current_balance}"


class CreateLoanSerializer(serializers.Serializer):
    """Serializer for creating a loan."""

    name = serializers.CharField(max_length=200)
    liability_type = serializers.ChoiceField(choices=Liability.LiabilityType.choices)
    principal = MoneyField()
    currency_code = CurrencyField()
    interest_rate = serializers.DecimalField(max_digits=6, decimal_places=4)
    payment_amount = MoneyField()
    payment_frequency = serializers.ChoiceField(choices=Loan.PaymentFrequency.choices)
    start_date = serializers.DateField(required=False, allow_null=True)
    expected_payoff_date = serializers.DateField(required=False, allow_null=True)
    next_payment_date = serializers.DateField(required=False, allow_null=True)
    lender = serializers.CharField(max_length=100, required=False, allow_null=True)
    account_number_masked = serializers.CharField(max_length=50, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    linked_account_id = serializers.UUIDField(required=False, allow_null=True)

    def create(self, validated_data):
        """Create a new loan."""
        principal = validated_data.pop("principal")
        validated_data["original_principal"] = principal
        validated_data["current_balance"] = principal
        return Loan.objects.create(**validated_data)


class RecordLoanPaymentSerializer(serializers.Serializer):
    """Serializer for recording a loan payment."""

    principal_amount = MoneyField()
    interest_amount = MoneyField(required=False, allow_null=True)


# =============================================================================
# Report Serializers
# =============================================================================


class NetWorthSerializer(serializers.Serializer):
    """Serializer for net worth report."""

    total_assets = serializers.DecimalField(max_digits=19, decimal_places=4)
    total_liabilities = serializers.DecimalField(max_digits=19, decimal_places=4)
    net_worth = serializers.DecimalField(max_digits=19, decimal_places=4)
    account_balances = serializers.DecimalField(max_digits=19, decimal_places=4)
    asset_count = serializers.IntegerField()
    liability_count = serializers.IntegerField()
    account_count = serializers.IntegerField()
    currency_code = serializers.CharField()
    calculated_at = serializers.DateTimeField()


class CashFlowSerializer(serializers.Serializer):
    """Serializer for cash flow report."""

    total_income = serializers.DecimalField(max_digits=19, decimal_places=4)
    total_expenses = serializers.DecimalField(max_digits=19, decimal_places=4)
    net_cash_flow = serializers.DecimalField(max_digits=19, decimal_places=4)
    income_by_category = serializers.DictField(
        child=serializers.DecimalField(max_digits=19, decimal_places=4)
    )
    expenses_by_category = serializers.DictField(
        child=serializers.DecimalField(max_digits=19, decimal_places=4)
    )
    currency_code = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
