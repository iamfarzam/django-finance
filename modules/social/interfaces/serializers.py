"""DRF serializers for the social finance module."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, ClassVar
from uuid import UUID

from rest_framework import serializers

from shared.serializers import FieldPermissionMixin


# =============================================================================
# Contact Serializers
# =============================================================================


class ContactSerializer(FieldPermissionMixin, serializers.Serializer):
    """Serializer for Contact DTO.

    Includes field-level permissions for premium features.
    """

    # Premium field permissions - sensitive contact info
    premium_fields: ClassVar[dict[str, str]] = {
        "email": "social.full",
        "phone": "social.full",
        "notes": "social.full",
        "linked_user_id": "social.full",
    }

    # Masking for non-premium users
    masked_fields: ClassVar[dict[str, Any]] = {
        "email": "***@***.***",
        "phone": "***-***-****",
    }

    id = serializers.UUIDField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=50, required=False, allow_null=True)
    avatar_url = serializers.URLField(read_only=True)
    notes = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField(read_only=True)
    linked_user_id = serializers.UUIDField(read_only=True, allow_null=True)
    share_status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreateContactSerializer(serializers.Serializer):
    """Serializer for creating a contact."""

    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=50, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)


class UpdateContactSerializer(serializers.Serializer):
    """Serializer for updating a contact."""

    name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=50, required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)


# =============================================================================
# Contact Group Serializers
# =============================================================================


class ContactGroupSerializer(serializers.Serializer):
    """Serializer for ContactGroup DTO."""

    id = serializers.UUIDField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_null=True)
    member_ids = serializers.ListField(
        child=serializers.UUIDField(), read_only=True
    )
    member_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreateContactGroupSerializer(serializers.Serializer):
    """Serializer for creating a contact group."""

    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_null=True)
    member_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )


class AddGroupMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to a group."""

    contact_id = serializers.UUIDField()


# =============================================================================
# Peer Debt Serializers
# =============================================================================


class PeerDebtSerializer(serializers.Serializer):
    """Serializer for PeerDebt DTO."""

    id = serializers.UUIDField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)
    contact_id = serializers.UUIDField()
    contact_name = serializers.CharField(read_only=True, allow_null=True)
    direction = serializers.ChoiceField(choices=["lent", "borrowed"])
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
    settled_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    remaining_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    description = serializers.CharField(required=False, allow_null=True)
    debt_date = serializers.DateField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.CharField(read_only=True)
    linked_transaction_id = serializers.UUIDField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreatePeerDebtSerializer(serializers.Serializer):
    """Serializer for creating a peer debt."""

    contact_id = serializers.UUIDField()
    direction = serializers.ChoiceField(choices=["lent", "borrowed"])
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal("0.01"))
    currency_code = serializers.CharField(max_length=3, default="USD")
    description = serializers.CharField(required=False, allow_null=True)
    debt_date = serializers.DateField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    linked_transaction_id = serializers.UUIDField(required=False, allow_null=True)


class SettleDebtSerializer(serializers.Serializer):
    """Serializer for settling a debt."""

    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal("0.01"))
    settlement_id = serializers.UUIDField(required=False, allow_null=True)


# =============================================================================
# Expense Group Serializers
# =============================================================================


class ExpenseGroupSerializer(serializers.Serializer):
    """Serializer for ExpenseGroup DTO."""

    id = serializers.UUIDField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_null=True)
    default_currency = serializers.CharField(max_length=3)
    member_contact_ids = serializers.ListField(
        child=serializers.UUIDField(), read_only=True
    )
    include_self = serializers.BooleanField()
    total_members = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CreateExpenseGroupSerializer(serializers.Serializer):
    """Serializer for creating an expense group."""

    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_null=True)
    default_currency = serializers.CharField(max_length=3, default="USD")
    member_contact_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    include_self = serializers.BooleanField(default=True)


class AddExpenseGroupMemberSerializer(serializers.Serializer):
    """Serializer for adding a member to an expense group."""

    contact_id = serializers.UUIDField()


# =============================================================================
# Group Expense Serializers
# =============================================================================


class ExpenseSplitSerializer(serializers.Serializer):
    """Serializer for ExpenseSplit DTO."""

    id = serializers.UUIDField(read_only=True)
    expense_id = serializers.UUIDField(read_only=True)
    contact_id = serializers.UUIDField(allow_null=True)
    is_owner = serializers.BooleanField()
    share_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    settled_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    remaining_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    status = serializers.CharField(read_only=True)


class GroupExpenseSerializer(serializers.Serializer):
    """Serializer for GroupExpense DTO."""

    id = serializers.UUIDField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)
    group_id = serializers.UUIDField()
    description = serializers.CharField(max_length=500)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
    paid_by_contact_id = serializers.UUIDField(allow_null=True)
    paid_by_owner = serializers.BooleanField()
    split_method = serializers.ChoiceField(choices=["equal", "exact"])
    expense_date = serializers.DateField()
    splits = ExpenseSplitSerializer(many=True, read_only=True)
    status = serializers.CharField(read_only=True)
    notes = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ExactSplitSerializer(serializers.Serializer):
    """Serializer for exact split entry."""

    contact_id = serializers.UUIDField(allow_null=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)


class CreateGroupExpenseSerializer(serializers.Serializer):
    """Serializer for creating a group expense."""

    group_id = serializers.UUIDField()
    description = serializers.CharField(max_length=500)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal("0.01"))
    currency_code = serializers.CharField(max_length=3, default="USD")
    paid_by_owner = serializers.BooleanField(default=True)
    paid_by_contact_id = serializers.UUIDField(required=False, allow_null=True)
    split_method = serializers.ChoiceField(choices=["equal", "exact"], default="equal")
    expense_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    exact_splits = ExactSplitSerializer(many=True, required=False)

    def validate(self, data):
        """Validate the expense creation data."""
        if not data.get("paid_by_owner") and not data.get("paid_by_contact_id"):
            raise serializers.ValidationError(
                "Either paid_by_owner must be True or paid_by_contact_id must be provided"
            )
        return data


# =============================================================================
# Settlement Serializers
# =============================================================================


class SettlementSerializer(serializers.Serializer):
    """Serializer for Settlement DTO."""

    id = serializers.UUIDField(read_only=True)
    tenant_id = serializers.UUIDField(read_only=True)
    from_contact_id = serializers.UUIDField(allow_null=True)
    to_contact_id = serializers.UUIDField(allow_null=True)
    from_is_owner = serializers.BooleanField()
    to_is_owner = serializers.BooleanField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
    method = serializers.CharField(max_length=50)
    settlement_date = serializers.DateField()
    linked_debt_ids = serializers.ListField(
        child=serializers.UUIDField(), read_only=True
    )
    linked_split_ids = serializers.ListField(
        child=serializers.UUIDField(), read_only=True
    )
    notes = serializers.CharField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class CreateSettlementSerializer(serializers.Serializer):
    """Serializer for creating a settlement."""

    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal("0.01"))
    currency_code = serializers.CharField(max_length=3, default="USD")
    owner_pays = serializers.BooleanField(default=False)
    owner_receives = serializers.BooleanField(default=False)
    contact_id = serializers.UUIDField()
    method = serializers.CharField(max_length=50, default="cash")
    settlement_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_null=True)
    linked_debt_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )
    linked_split_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )

    def validate(self, data):
        """Validate the settlement creation data."""
        if data.get("owner_pays") and data.get("owner_receives"):
            raise serializers.ValidationError(
                "Cannot set both owner_pays and owner_receives to True"
            )
        if not data.get("owner_pays") and not data.get("owner_receives"):
            raise serializers.ValidationError(
                "Must set either owner_pays or owner_receives to True"
            )
        return data


# =============================================================================
# Balance Serializers
# =============================================================================


class ContactBalanceSerializer(serializers.Serializer):
    """Serializer for ContactBalance DTO."""

    contact_id = serializers.UUIDField()
    contact_name = serializers.CharField(allow_null=True)
    currency_code = serializers.CharField(max_length=3)
    total_lent = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_borrowed = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_settled_to_them = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_settled_from_them = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    they_owe_you = serializers.DecimalField(max_digits=15, decimal_places=2)
    you_owe_them = serializers.DecimalField(max_digits=15, decimal_places=2)


class GroupBalanceEntrySerializer(serializers.Serializer):
    """Serializer for GroupBalanceEntry DTO."""

    from_contact_id = serializers.UUIDField(allow_null=True)
    from_name = serializers.CharField(allow_null=True)
    to_contact_id = serializers.UUIDField(allow_null=True)
    to_name = serializers.CharField(allow_null=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)


class GroupBalanceSerializer(serializers.Serializer):
    """Serializer for GroupBalance DTO."""

    group_id = serializers.UUIDField()
    group_name = serializers.CharField()
    currency_code = serializers.CharField(max_length=3)
    entries = GroupBalanceEntrySerializer(many=True)
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)


class SettlementSuggestionSerializer(serializers.Serializer):
    """Serializer for SettlementSuggestion DTO."""

    from_contact_id = serializers.UUIDField(allow_null=True)
    from_name = serializers.CharField(allow_null=True)
    to_contact_id = serializers.UUIDField(allow_null=True)
    to_name = serializers.CharField(allow_null=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency_code = serializers.CharField(max_length=3)
