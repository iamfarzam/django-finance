"""DRF views for the social finance module."""

from __future__ import annotations

from dataclasses import asdict

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from modules.social.application.dto import (
    CreateContactCommand,
    CreateContactGroupCommand,
    CreateExpenseGroupCommand,
    CreateGroupExpenseCommand,
    CreatePeerDebtCommand,
    CreateSettlementCommand,
    SettleDebtCommand,
    UpdateContactCommand,
)
from modules.social.application.use_cases import (
    BalanceUseCases,
    ContactGroupUseCases,
    ContactUseCases,
    ExpenseGroupUseCases,
    GroupExpenseUseCases,
    PeerDebtUseCases,
    SettlementUseCases,
)
from modules.social.domain.exceptions import (
    ContactNotFoundError,
    DebtAlreadySettledError,
    DebtNotFoundError,
    ExpenseGroupNotFoundError,
    GroupExpenseNotFoundError,
    InvalidSplitTotalError,
)
from modules.social.infrastructure.repositories import (
    DjangoContactGroupRepository,
    DjangoContactRepository,
    DjangoExpenseGroupRepository,
    DjangoGroupExpenseRepository,
    DjangoPeerDebtRepository,
    DjangoSettlementRepository,
)
from modules.social.interfaces.serializers import (
    AddExpenseGroupMemberSerializer,
    AddGroupMemberSerializer,
    ContactBalanceSerializer,
    ContactGroupSerializer,
    ContactSerializer,
    CreateContactGroupSerializer,
    CreateContactSerializer,
    CreateExpenseGroupSerializer,
    CreateGroupExpenseSerializer,
    CreatePeerDebtSerializer,
    CreateSettlementSerializer,
    ExpenseGroupSerializer,
    GroupBalanceSerializer,
    GroupExpenseSerializer,
    PeerDebtSerializer,
    SettleDebtSerializer,
    SettlementSerializer,
    SettlementSuggestionSerializer,
    UpdateContactSerializer,
)


def get_tenant_id(request: Request):
    """Get tenant ID from request user."""
    return request.user.tenant_id


# =============================================================================
# Contact Views
# =============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="List contacts",
        description="List all contacts for the current tenant.",
        tags=["Social - Contacts"],
    ),
    create=extend_schema(
        summary="Create contact",
        description="Create a new contact.",
        tags=["Social - Contacts"],
    ),
    retrieve=extend_schema(
        summary="Get contact",
        description="Get a contact by ID.",
        tags=["Social - Contacts"],
    ),
    update=extend_schema(
        summary="Update contact",
        description="Update a contact.",
        tags=["Social - Contacts"],
    ),
    partial_update=extend_schema(
        summary="Partial update contact",
        description="Partially update a contact.",
        tags=["Social - Contacts"],
    ),
    destroy=extend_schema(
        summary="Delete contact",
        description="Delete a contact.",
        tags=["Social - Contacts"],
    ),
)
class ContactViewSet(viewsets.ViewSet):
    """ViewSet for Contact CRUD operations."""

    permission_classes = [IsAuthenticated]

    def get_use_cases(self) -> ContactUseCases:
        """Get contact use cases."""
        return ContactUseCases(
            contact_repo=DjangoContactRepository(),
        )

    def list(self, request: Request) -> Response:
        """List all contacts."""
        use_cases = self.get_use_cases()
        contacts = use_cases.list_contacts(get_tenant_id(request))
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new contact."""
        serializer = CreateContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreateContactCommand(
            tenant_id=get_tenant_id(request),
            **serializer.validated_data,
        )

        use_cases = self.get_use_cases()
        contact = use_cases.create_contact(command)
        return Response(
            ContactSerializer(contact).data, status=status.HTTP_201_CREATED
        )

    def retrieve(self, request: Request, pk=None) -> Response:
        """Get a contact by ID."""
        use_cases = self.get_use_cases()
        contact = use_cases.get_contact(pk, get_tenant_id(request))
        if not contact:
            return Response(
                {"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(ContactSerializer(contact).data)

    def update(self, request: Request, pk=None) -> Response:
        """Update a contact."""
        serializer = UpdateContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = UpdateContactCommand(
            contact_id=pk,
            **serializer.validated_data,
        )

        try:
            use_cases = self.get_use_cases()
            contact = use_cases.update_contact(command, get_tenant_id(request))
            return Response(ContactSerializer(contact).data)
        except ContactNotFoundError:
            return Response(
                {"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND
            )

    def partial_update(self, request: Request, pk=None) -> Response:
        """Partially update a contact."""
        return self.update(request, pk)

    def destroy(self, request: Request, pk=None) -> Response:
        """Delete a contact."""
        use_cases = self.get_use_cases()
        deleted = use_cases.delete_contact(pk, get_tenant_id(request))
        if not deleted:
            return Response(
                {"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Archive contact",
        description="Archive a contact.",
        tags=["Social - Contacts"],
    )
    @action(detail=True, methods=["post"])
    def archive(self, request: Request, pk=None) -> Response:
        """Archive a contact."""
        try:
            use_cases = self.get_use_cases()
            contact = use_cases.archive_contact(pk, get_tenant_id(request))
            return Response(ContactSerializer(contact).data)
        except ContactNotFoundError:
            return Response(
                {"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND
            )


# =============================================================================
# Contact Group Views
# =============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="List contact groups",
        description="List all contact groups for the current tenant.",
        tags=["Social - Contact Groups"],
    ),
    create=extend_schema(
        summary="Create contact group",
        description="Create a new contact group.",
        tags=["Social - Contact Groups"],
    ),
    retrieve=extend_schema(
        summary="Get contact group",
        description="Get a contact group by ID.",
        tags=["Social - Contact Groups"],
    ),
    destroy=extend_schema(
        summary="Delete contact group",
        description="Delete a contact group.",
        tags=["Social - Contact Groups"],
    ),
)
class ContactGroupViewSet(viewsets.ViewSet):
    """ViewSet for ContactGroup CRUD operations."""

    permission_classes = [IsAuthenticated]

    def get_use_cases(self) -> ContactGroupUseCases:
        """Get contact group use cases."""
        return ContactGroupUseCases(
            group_repo=DjangoContactGroupRepository(),
            contact_repo=DjangoContactRepository(),
        )

    def list(self, request: Request) -> Response:
        """List all contact groups."""
        use_cases = self.get_use_cases()
        groups = use_cases.list_groups(get_tenant_id(request))
        serializer = ContactGroupSerializer(groups, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new contact group."""
        serializer = CreateContactGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreateContactGroupCommand(
            tenant_id=get_tenant_id(request),
            **serializer.validated_data,
        )

        use_cases = self.get_use_cases()
        group = use_cases.create_group(command)
        return Response(
            ContactGroupSerializer(group).data, status=status.HTTP_201_CREATED
        )

    def retrieve(self, request: Request, pk=None) -> Response:
        """Get a contact group by ID."""
        use_cases = self.get_use_cases()
        group = use_cases.get_group(pk, get_tenant_id(request))
        if not group:
            return Response(
                {"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(ContactGroupSerializer(group).data)

    def destroy(self, request: Request, pk=None) -> Response:
        """Delete a contact group."""
        use_cases = self.get_use_cases()
        deleted = use_cases.group_repo.delete(pk, get_tenant_id(request))
        if not deleted:
            return Response(
                {"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Add member to group",
        description="Add a contact to a contact group.",
        tags=["Social - Contact Groups"],
        request=AddGroupMemberSerializer,
    )
    @action(detail=True, methods=["post"])
    def add_member(self, request: Request, pk=None) -> Response:
        """Add a member to the group."""
        serializer = AddGroupMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            use_cases = self.get_use_cases()
            group = use_cases.add_member(
                pk, serializer.validated_data["contact_id"], get_tenant_id(request)
            )
            return Response(ContactGroupSerializer(group).data)
        except ContactNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Remove member from group",
        description="Remove a contact from a contact group.",
        tags=["Social - Contact Groups"],
        request=AddGroupMemberSerializer,
    )
    @action(detail=True, methods=["post"])
    def remove_member(self, request: Request, pk=None) -> Response:
        """Remove a member from the group."""
        serializer = AddGroupMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            use_cases = self.get_use_cases()
            group = use_cases.remove_member(
                pk, serializer.validated_data["contact_id"], get_tenant_id(request)
            )
            return Response(ContactGroupSerializer(group).data)
        except ContactNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# Peer Debt Views
# =============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="List peer debts",
        description="List all peer debts for the current tenant.",
        tags=["Social - Peer Debts"],
    ),
    create=extend_schema(
        summary="Create peer debt",
        description="Create a new peer debt.",
        tags=["Social - Peer Debts"],
    ),
    retrieve=extend_schema(
        summary="Get peer debt",
        description="Get a peer debt by ID.",
        tags=["Social - Peer Debts"],
    ),
    destroy=extend_schema(
        summary="Delete peer debt",
        description="Delete a peer debt.",
        tags=["Social - Peer Debts"],
    ),
)
class PeerDebtViewSet(viewsets.ViewSet):
    """ViewSet for PeerDebt CRUD operations."""

    permission_classes = [IsAuthenticated]

    def get_use_cases(self) -> PeerDebtUseCases:
        """Get peer debt use cases."""
        return PeerDebtUseCases(
            debt_repo=DjangoPeerDebtRepository(),
            contact_repo=DjangoContactRepository(),
            settlement_repo=DjangoSettlementRepository(),
        )

    def list(self, request: Request) -> Response:
        """List all peer debts."""
        use_cases = self.get_use_cases()
        debts = use_cases.list_debts(get_tenant_id(request))
        serializer = PeerDebtSerializer(debts, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new peer debt."""
        serializer = CreatePeerDebtSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreatePeerDebtCommand(
            tenant_id=get_tenant_id(request),
            **serializer.validated_data,
        )

        try:
            use_cases = self.get_use_cases()
            debt = use_cases.create_debt(command)
            return Response(
                PeerDebtSerializer(debt).data, status=status.HTTP_201_CREATED
            )
        except ContactNotFoundError:
            return Response(
                {"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND
            )

    def retrieve(self, request: Request, pk=None) -> Response:
        """Get a peer debt by ID."""
        use_cases = self.get_use_cases()
        debt = use_cases.get_debt(pk, get_tenant_id(request))
        if not debt:
            return Response(
                {"detail": "Debt not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(PeerDebtSerializer(debt).data)

    def destroy(self, request: Request, pk=None) -> Response:
        """Delete a peer debt."""
        use_cases = self.get_use_cases()
        deleted = use_cases.debt_repo.delete(pk, get_tenant_id(request))
        if not deleted:
            return Response(
                {"detail": "Debt not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="List active debts",
        description="List all active (unsettled) peer debts.",
        tags=["Social - Peer Debts"],
    )
    @action(detail=False, methods=["get"])
    def active(self, request: Request) -> Response:
        """List active debts."""
        use_cases = self.get_use_cases()
        debts = use_cases.list_active_debts(get_tenant_id(request))
        serializer = PeerDebtSerializer(debts, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Settle debt",
        description="Partially or fully settle a peer debt.",
        tags=["Social - Peer Debts"],
        request=SettleDebtSerializer,
    )
    @action(detail=True, methods=["post"])
    def settle(self, request: Request, pk=None) -> Response:
        """Settle a debt."""
        serializer = SettleDebtSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = SettleDebtCommand(
            debt_id=pk,
            amount=serializer.validated_data["amount"],
            settlement_id=serializer.validated_data.get("settlement_id"),
        )

        try:
            use_cases = self.get_use_cases()
            debt = use_cases.settle_debt(command, get_tenant_id(request))
            return Response(PeerDebtSerializer(debt).data)
        except DebtNotFoundError:
            return Response(
                {"detail": "Debt not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except DebtAlreadySettledError:
            return Response(
                {"detail": "Debt is already settled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Cancel debt",
        description="Cancel a peer debt.",
        tags=["Social - Peer Debts"],
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request: Request, pk=None) -> Response:
        """Cancel a debt."""
        try:
            use_cases = self.get_use_cases()
            debt = use_cases.cancel_debt(pk, get_tenant_id(request))
            return Response(PeerDebtSerializer(debt).data)
        except DebtNotFoundError:
            return Response(
                {"detail": "Debt not found."}, status=status.HTTP_404_NOT_FOUND
            )


# =============================================================================
# Expense Group Views
# =============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="List expense groups",
        description="List all expense groups for the current tenant.",
        tags=["Social - Expense Groups"],
    ),
    create=extend_schema(
        summary="Create expense group",
        description="Create a new expense group.",
        tags=["Social - Expense Groups"],
    ),
    retrieve=extend_schema(
        summary="Get expense group",
        description="Get an expense group by ID.",
        tags=["Social - Expense Groups"],
    ),
    destroy=extend_schema(
        summary="Delete expense group",
        description="Delete an expense group.",
        tags=["Social - Expense Groups"],
    ),
)
class ExpenseGroupViewSet(viewsets.ViewSet):
    """ViewSet for ExpenseGroup CRUD operations."""

    permission_classes = [IsAuthenticated]

    def get_use_cases(self) -> ExpenseGroupUseCases:
        """Get expense group use cases."""
        return ExpenseGroupUseCases(
            group_repo=DjangoExpenseGroupRepository(),
            contact_repo=DjangoContactRepository(),
            expense_repo=DjangoGroupExpenseRepository(),
        )

    def list(self, request: Request) -> Response:
        """List all expense groups."""
        use_cases = self.get_use_cases()
        groups = use_cases.list_groups(get_tenant_id(request))
        serializer = ExpenseGroupSerializer(groups, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new expense group."""
        serializer = CreateExpenseGroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreateExpenseGroupCommand(
            tenant_id=get_tenant_id(request),
            **serializer.validated_data,
        )

        use_cases = self.get_use_cases()
        group = use_cases.create_group(command)
        return Response(
            ExpenseGroupSerializer(group).data, status=status.HTTP_201_CREATED
        )

    def retrieve(self, request: Request, pk=None) -> Response:
        """Get an expense group by ID."""
        use_cases = self.get_use_cases()
        group = use_cases.get_group(pk, get_tenant_id(request))
        if not group:
            return Response(
                {"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(ExpenseGroupSerializer(group).data)

    def destroy(self, request: Request, pk=None) -> Response:
        """Delete an expense group."""
        use_cases = self.get_use_cases()
        deleted = use_cases.group_repo.delete(pk, get_tenant_id(request))
        if not deleted:
            return Response(
                {"detail": "Group not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Add member to expense group",
        description="Add a contact to an expense group.",
        tags=["Social - Expense Groups"],
        request=AddExpenseGroupMemberSerializer,
    )
    @action(detail=True, methods=["post"])
    def add_member(self, request: Request, pk=None) -> Response:
        """Add a member to the expense group."""
        serializer = AddExpenseGroupMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            use_cases = self.get_use_cases()
            group = use_cases.add_member(
                pk, serializer.validated_data["contact_id"], get_tenant_id(request)
            )
            return Response(ExpenseGroupSerializer(group).data)
        except (ExpenseGroupNotFoundError, ContactNotFoundError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        summary="Remove member from expense group",
        description="Remove a contact from an expense group.",
        tags=["Social - Expense Groups"],
        request=AddExpenseGroupMemberSerializer,
    )
    @action(detail=True, methods=["post"])
    def remove_member(self, request: Request, pk=None) -> Response:
        """Remove a member from the expense group."""
        serializer = AddExpenseGroupMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            use_cases = self.get_use_cases()
            group = use_cases.remove_member(
                pk, serializer.validated_data["contact_id"], get_tenant_id(request)
            )
            return Response(ExpenseGroupSerializer(group).data)
        except ExpenseGroupNotFoundError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# Group Expense Views
# =============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="List group expenses",
        description="List all group expenses for the current tenant.",
        tags=["Social - Group Expenses"],
    ),
    create=extend_schema(
        summary="Create group expense",
        description="Create a new group expense with automatic splitting.",
        tags=["Social - Group Expenses"],
    ),
    retrieve=extend_schema(
        summary="Get group expense",
        description="Get a group expense by ID.",
        tags=["Social - Group Expenses"],
    ),
    destroy=extend_schema(
        summary="Delete group expense",
        description="Delete a group expense.",
        tags=["Social - Group Expenses"],
    ),
)
class GroupExpenseViewSet(viewsets.ViewSet):
    """ViewSet for GroupExpense CRUD operations."""

    permission_classes = [IsAuthenticated]

    def get_use_cases(self) -> GroupExpenseUseCases:
        """Get group expense use cases."""
        return GroupExpenseUseCases(
            expense_repo=DjangoGroupExpenseRepository(),
            group_repo=DjangoExpenseGroupRepository(),
            contact_repo=DjangoContactRepository(),
        )

    def list(self, request: Request) -> Response:
        """List all group expenses."""
        use_cases = self.get_use_cases()
        # Get expenses for a specific group if provided
        group_id = request.query_params.get("group_id")
        if group_id:
            expenses = use_cases.list_expenses_by_group(group_id, get_tenant_id(request))
        else:
            expenses = [
                use_cases._to_dto(e)
                for e in use_cases.expense_repo.get_all(get_tenant_id(request))
            ]
        serializer = GroupExpenseSerializer(expenses, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new group expense."""
        serializer = CreateGroupExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        exact_splits = None
        if data.get("exact_splits"):
            exact_splits = {
                s["contact_id"]: s["amount"] for s in data["exact_splits"]
            }

        command = CreateGroupExpenseCommand(
            tenant_id=get_tenant_id(request),
            group_id=data["group_id"],
            description=data["description"],
            total_amount=data["total_amount"],
            currency_code=data.get("currency_code", "USD"),
            paid_by_owner=data.get("paid_by_owner", True),
            paid_by_contact_id=data.get("paid_by_contact_id"),
            split_method=data.get("split_method", "equal"),
            expense_date=data.get("expense_date"),
            notes=data.get("notes"),
            exact_splits=exact_splits,
        )

        try:
            use_cases = self.get_use_cases()
            expense = use_cases.create_expense(command)
            return Response(
                GroupExpenseSerializer(expense).data, status=status.HTTP_201_CREATED
            )
        except ExpenseGroupNotFoundError:
            return Response(
                {"detail": "Expense group not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except InvalidSplitTotalError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request: Request, pk=None) -> Response:
        """Get a group expense by ID."""
        use_cases = self.get_use_cases()
        expense = use_cases.get_expense(pk, get_tenant_id(request))
        if not expense:
            return Response(
                {"detail": "Expense not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(GroupExpenseSerializer(expense).data)

    def destroy(self, request: Request, pk=None) -> Response:
        """Delete a group expense."""
        use_cases = self.get_use_cases()
        deleted = use_cases.expense_repo.delete(pk, get_tenant_id(request))
        if not deleted:
            return Response(
                {"detail": "Expense not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        summary="Cancel expense",
        description="Cancel a group expense.",
        tags=["Social - Group Expenses"],
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request: Request, pk=None) -> Response:
        """Cancel an expense."""
        try:
            use_cases = self.get_use_cases()
            expense = use_cases.cancel_expense(pk, get_tenant_id(request))
            return Response(GroupExpenseSerializer(expense).data)
        except GroupExpenseNotFoundError:
            return Response(
                {"detail": "Expense not found."}, status=status.HTTP_404_NOT_FOUND
            )


# =============================================================================
# Settlement Views
# =============================================================================


@extend_schema_view(
    list=extend_schema(
        summary="List settlements",
        description="List all settlements for the current tenant.",
        tags=["Social - Settlements"],
    ),
    create=extend_schema(
        summary="Create settlement",
        description="Record a new settlement payment.",
        tags=["Social - Settlements"],
    ),
    retrieve=extend_schema(
        summary="Get settlement",
        description="Get a settlement by ID.",
        tags=["Social - Settlements"],
    ),
    destroy=extend_schema(
        summary="Delete settlement",
        description="Delete a settlement.",
        tags=["Social - Settlements"],
    ),
)
class SettlementViewSet(viewsets.ViewSet):
    """ViewSet for Settlement CRUD operations."""

    permission_classes = [IsAuthenticated]

    def get_use_cases(self) -> SettlementUseCases:
        """Get settlement use cases."""
        return SettlementUseCases(
            settlement_repo=DjangoSettlementRepository(),
            debt_repo=DjangoPeerDebtRepository(),
            expense_repo=DjangoGroupExpenseRepository(),
            contact_repo=DjangoContactRepository(),
        )

    def list(self, request: Request) -> Response:
        """List all settlements."""
        use_cases = self.get_use_cases()
        settlements = use_cases.list_settlements(get_tenant_id(request))
        serializer = SettlementSerializer(settlements, many=True)
        return Response(serializer.data)

    def create(self, request: Request) -> Response:
        """Create a new settlement."""
        serializer = CreateSettlementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = CreateSettlementCommand(
            tenant_id=get_tenant_id(request),
            **serializer.validated_data,
        )

        use_cases = self.get_use_cases()
        settlement = use_cases.create_settlement(command)
        return Response(
            SettlementSerializer(settlement).data, status=status.HTTP_201_CREATED
        )

    def retrieve(self, request: Request, pk=None) -> Response:
        """Get a settlement by ID."""
        use_cases = self.get_use_cases()
        settlement = use_cases.get_settlement(pk, get_tenant_id(request))
        if not settlement:
            return Response(
                {"detail": "Settlement not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(SettlementSerializer(settlement).data)

    def destroy(self, request: Request, pk=None) -> Response:
        """Delete a settlement."""
        use_cases = self.get_use_cases()
        deleted = use_cases.settlement_repo.delete(pk, get_tenant_id(request))
        if not deleted:
            return Response(
                {"detail": "Settlement not found."}, status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


# =============================================================================
# Balance Views
# =============================================================================


@extend_schema(tags=["Social - Balances"])
class BalanceViewSet(viewsets.ViewSet):
    """ViewSet for balance calculations."""

    permission_classes = [IsAuthenticated]

    def get_use_cases(self) -> BalanceUseCases:
        """Get balance use cases."""
        return BalanceUseCases(
            debt_repo=DjangoPeerDebtRepository(),
            settlement_repo=DjangoSettlementRepository(),
            expense_repo=DjangoGroupExpenseRepository(),
            group_repo=DjangoExpenseGroupRepository(),
            contact_repo=DjangoContactRepository(),
        )

    @extend_schema(
        summary="List contact balances",
        description="Get balances with all contacts.",
        parameters=[
            OpenApiParameter(
                name="currency",
                description="Currency code (default: USD)",
                required=False,
                type=str,
            ),
        ],
    )
    def list(self, request: Request) -> Response:
        """List all contact balances."""
        currency = request.query_params.get("currency", "USD")
        use_cases = self.get_use_cases()
        balances = use_cases.get_all_contact_balances(get_tenant_id(request), currency)
        serializer = ContactBalanceSerializer(balances, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get contact balance",
        description="Get balance with a specific contact.",
        parameters=[
            OpenApiParameter(
                name="currency",
                description="Currency code (default: USD)",
                required=False,
                type=str,
            ),
        ],
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Get balance with a specific contact."""
        currency = request.query_params.get("currency", "USD")
        try:
            use_cases = self.get_use_cases()
            balance = use_cases.get_contact_balance(pk, get_tenant_id(request), currency)
            return Response(ContactBalanceSerializer(balance).data)
        except ContactNotFoundError:
            return Response(
                {"detail": "Contact not found."}, status=status.HTTP_404_NOT_FOUND
            )

    @extend_schema(
        summary="Get group balance",
        description="Get balance for an expense group.",
    )
    @action(detail=False, methods=["get"], url_path="group/(?P<group_id>[^/.]+)")
    def group_balance(self, request: Request, group_id=None) -> Response:
        """Get group balance."""
        try:
            use_cases = self.get_use_cases()
            balance = use_cases.get_group_balance(group_id, get_tenant_id(request))
            return Response(GroupBalanceSerializer(balance).data)
        except ExpenseGroupNotFoundError:
            return Response(
                {"detail": "Expense group not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @extend_schema(
        summary="Get settlement suggestions",
        description="Get suggestions for settling all balances.",
        parameters=[
            OpenApiParameter(
                name="currency",
                description="Currency code (default: USD)",
                required=False,
                type=str,
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def suggestions(self, request: Request) -> Response:
        """Get settlement suggestions."""
        currency = request.query_params.get("currency", "USD")
        use_cases = self.get_use_cases()
        suggestions = use_cases.get_settlement_suggestions(
            get_tenant_id(request), currency
        )
        serializer = SettlementSuggestionSerializer(suggestions, many=True)
        return Response(serializer.data)
