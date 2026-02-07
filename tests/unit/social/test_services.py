"""Unit tests for social finance domain services."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from modules.social.domain.entities import (
    ExpenseSplit,
    GroupExpense,
    PeerDebt,
    Settlement,
)
from modules.social.domain.enums import (
    DebtDirection,
    DebtStatus,
    ExpenseStatus,
    SplitMethod,
    SplitStatus,
)
from modules.social.domain.services import (
    ContactBalance,
    DebtCalculator,
    GroupBalanceCalculator,
    GroupBalanceEntry,
    GroupBalanceResult,
    SettlementSuggestionService,
    SimplifiedDebt,
    SimplifyDebtsService,
)


class TestContactBalance:
    """Tests for ContactBalance dataclass."""

    def test_net_balance_positive(self):
        """Test net balance when they owe you."""
        balance = ContactBalance(
            contact_id=uuid4(),
            currency_code="USD",
            total_lent=Decimal("100"),
            total_borrowed=Decimal("0"),
            total_settled_to_them=Decimal("0"),
            total_settled_from_them=Decimal("0"),
        )

        assert balance.net_balance == Decimal("100")
        assert balance.they_owe_you == Decimal("100")
        assert balance.you_owe_them == Decimal("0")

    def test_net_balance_negative(self):
        """Test net balance when you owe them."""
        balance = ContactBalance(
            contact_id=uuid4(),
            currency_code="USD",
            total_lent=Decimal("0"),
            total_borrowed=Decimal("50"),
            total_settled_to_them=Decimal("0"),
            total_settled_from_them=Decimal("0"),
        )

        assert balance.net_balance == Decimal("-50")
        assert balance.they_owe_you == Decimal("0")
        assert balance.you_owe_them == Decimal("50")

    def test_net_balance_with_settlements(self):
        """Test net balance with settlements."""
        balance = ContactBalance(
            contact_id=uuid4(),
            currency_code="USD",
            total_lent=Decimal("100"),
            total_borrowed=Decimal("30"),
            total_settled_to_them=Decimal("20"),  # You paid them
            total_settled_from_them=Decimal("50"),  # They paid you
        )

        # Net = (lent - settled_from) - (borrowed - settled_to)
        # Net = (100 - 50) - (30 - 20) = 50 - 10 = 40
        assert balance.net_balance == Decimal("40")


class TestDebtCalculator:
    """Tests for DebtCalculator service."""

    def test_calculate_contact_balance_lent(self):
        """Test calculating balance for lent debts."""
        contact_id = uuid4()
        tenant_id = uuid4()

        debt = PeerDebt(
            id=uuid4(),
            tenant_id=tenant_id,
            contact_id=contact_id,
            direction=DebtDirection.LENT,
            amount=Decimal("100"),
            currency_code="USD",
            settled_amount=Decimal("0"),
            description=None,
            debt_date=date.today(),
            due_date=None,
            status=DebtStatus.ACTIVE,
            linked_transaction_id=None,
            notes=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        balance = DebtCalculator.calculate_contact_balance(
            debts=[debt],
            settlements=[],
            contact_id=contact_id,
            currency_code="USD",
        )

        assert balance.total_lent == Decimal("100")
        assert balance.net_balance == Decimal("100")

    def test_calculate_contact_balance_borrowed(self):
        """Test calculating balance for borrowed debts."""
        contact_id = uuid4()
        tenant_id = uuid4()

        debt = PeerDebt(
            id=uuid4(),
            tenant_id=tenant_id,
            contact_id=contact_id,
            direction=DebtDirection.BORROWED,
            amount=Decimal("75"),
            currency_code="USD",
            settled_amount=Decimal("0"),
            description=None,
            debt_date=date.today(),
            due_date=None,
            status=DebtStatus.ACTIVE,
            linked_transaction_id=None,
            notes=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        balance = DebtCalculator.calculate_contact_balance(
            debts=[debt],
            settlements=[],
            contact_id=contact_id,
            currency_code="USD",
        )

        assert balance.total_borrowed == Decimal("75")
        assert balance.net_balance == Decimal("-75")

    def test_calculate_contact_balance_with_settlement(self):
        """Test balance calculation including settlements."""
        contact_id = uuid4()
        tenant_id = uuid4()

        debt = PeerDebt(
            id=uuid4(),
            tenant_id=tenant_id,
            contact_id=contact_id,
            direction=DebtDirection.LENT,
            amount=Decimal("100"),
            currency_code="USD",
            settled_amount=Decimal("0"),
            description=None,
            debt_date=date.today(),
            due_date=None,
            status=DebtStatus.ACTIVE,
            linked_transaction_id=None,
            notes=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        settlement = Settlement(
            id=uuid4(),
            tenant_id=tenant_id,
            from_is_owner=False,
            from_contact_id=contact_id,
            to_is_owner=True,
            to_contact_id=None,
            amount=Decimal("30"),
            currency_code="USD",
            method="cash",
            settlement_date=date.today(),
            notes=None,
            created_at=datetime.now(timezone.utc),
        )

        balance = DebtCalculator.calculate_contact_balance(
            debts=[debt],
            settlements=[settlement],
            contact_id=contact_id,
            currency_code="USD",
        )

        assert balance.total_lent == Decimal("100")
        assert balance.total_settled_from_them == Decimal("30")
        assert balance.net_balance == Decimal("70")

    def test_calculate_skips_cancelled_debts(self):
        """Test that cancelled debts are skipped."""
        contact_id = uuid4()
        tenant_id = uuid4()

        debt = PeerDebt(
            id=uuid4(),
            tenant_id=tenant_id,
            contact_id=contact_id,
            direction=DebtDirection.LENT,
            amount=Decimal("100"),
            currency_code="USD",
            settled_amount=Decimal("0"),
            description=None,
            debt_date=date.today(),
            due_date=None,
            status=DebtStatus.CANCELLED,
            linked_transaction_id=None,
            notes=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        balance = DebtCalculator.calculate_contact_balance(
            debts=[debt],
            settlements=[],
            contact_id=contact_id,
            currency_code="USD",
        )

        assert balance.total_lent == Decimal("0")


class TestGroupBalanceCalculator:
    """Tests for GroupBalanceCalculator service."""

    def test_calculate_simple_group_balance(self):
        """Test simple group balance calculation."""
        tenant_id = uuid4()
        group_id = uuid4()
        contact_id = uuid4()

        expense = GroupExpense(
            id=uuid4(),
            tenant_id=tenant_id,
            group_id=group_id,
            description="Dinner",
            total_amount=Decimal("60"),
            currency_code="USD",
            paid_by_owner=True,
            paid_by_contact_id=None,
            split_method=SplitMethod.EQUAL,
            expense_date=date.today(),
            status=ExpenseStatus.ACTIVE,
            notes=None,
            splits=[
                ExpenseSplit(
                    id=uuid4(),
                    expense_id=uuid4(),
                    contact_id=None,
                    is_owner=True,
                    share_amount=Decimal("30"),
                    settled_amount=Decimal("0"),
                    status=SplitStatus.PENDING,
                ),
                ExpenseSplit(
                    id=uuid4(),
                    expense_id=uuid4(),
                    contact_id=contact_id,
                    is_owner=False,
                    share_amount=Decimal("30"),
                    settled_amount=Decimal("0"),
                    status=SplitStatus.PENDING,
                ),
            ],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = GroupBalanceCalculator.calculate([expense], "USD")

        assert result.total_expenses == Decimal("60")
        # Owner paid 60, owes 30 => net +30 (owed)
        # Contact paid 0, owes 30 => net -30 (owes)
        assert len(result.entries) == 1
        assert result.entries[0].from_contact_id == contact_id
        assert result.entries[0].to_contact_id is None  # Owner
        assert result.entries[0].amount == Decimal("30")

    def test_calculate_skips_cancelled_expenses(self):
        """Test that cancelled expenses are skipped."""
        expense = GroupExpense(
            id=uuid4(),
            tenant_id=uuid4(),
            group_id=uuid4(),
            description="Dinner",
            total_amount=Decimal("100"),
            currency_code="USD",
            paid_by_owner=True,
            paid_by_contact_id=None,
            split_method=SplitMethod.EQUAL,
            expense_date=date.today(),
            status=ExpenseStatus.CANCELLED,
            notes=None,
            splits=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        result = GroupBalanceCalculator.calculate([expense], "USD")

        assert result.total_expenses == Decimal("0")


class TestSimplifyDebtsService:
    """Tests for SimplifyDebtsService."""

    def test_simplify_two_person_debt(self):
        """Test simplifying debts between two people."""
        contact_id = uuid4()
        balances = {
            None: Decimal("50"),  # Owner is owed 50
            contact_id: Decimal("-50"),  # Contact owes 50
        }

        simplified = SimplifyDebtsService.simplify(balances)

        assert len(simplified) == 1
        assert simplified[0].from_contact_id == contact_id
        assert simplified[0].to_contact_id is None
        assert simplified[0].amount == Decimal("50")

    def test_simplify_three_person_chain(self):
        """Test simplifying debts with three people."""
        contact1 = uuid4()
        contact2 = uuid4()
        balances = {
            None: Decimal("30"),  # Owner is owed 30
            contact1: Decimal("-20"),  # Contact1 owes 20
            contact2: Decimal("-10"),  # Contact2 owes 10
        }

        simplified = SimplifyDebtsService.simplify(balances)

        assert len(simplified) == 2
        total_to_owner = sum(
            s.amount for s in simplified if s.to_contact_id is None
        )
        assert total_to_owner == Decimal("30")

    def test_simplify_no_debts(self):
        """Test simplifying when no debts exist."""
        balances = {
            None: Decimal("0"),
            uuid4(): Decimal("0"),
        }

        simplified = SimplifyDebtsService.simplify(balances)

        assert len(simplified) == 0

    def test_simplify_balanced_round_robin(self):
        """Test simplifying a balanced scenario."""
        contact1 = uuid4()
        contact2 = uuid4()
        balances = {
            None: Decimal("100"),  # Owner is owed 100
            contact1: Decimal("-50"),  # Contact1 owes 50
            contact2: Decimal("-50"),  # Contact2 owes 50
        }

        simplified = SimplifyDebtsService.simplify(balances)

        # Both contacts should pay owner
        assert len(simplified) == 2


class TestSettlementSuggestionService:
    """Tests for SettlementSuggestionService."""

    def test_suggest_for_positive_balance(self):
        """Test suggestion when contact owes you."""
        contact_id = uuid4()
        balance = ContactBalance(
            contact_id=contact_id,
            currency_code="USD",
            total_lent=Decimal("100"),
            total_borrowed=Decimal("0"),
        )

        suggestion = SettlementSuggestionService.suggest_for_contact(balance)

        assert suggestion is not None
        assert suggestion.from_contact_id == contact_id  # Contact pays
        assert suggestion.to_contact_id is None  # To owner
        assert suggestion.amount == Decimal("100")

    def test_suggest_for_negative_balance(self):
        """Test suggestion when you owe contact."""
        contact_id = uuid4()
        balance = ContactBalance(
            contact_id=contact_id,
            currency_code="USD",
            total_lent=Decimal("0"),
            total_borrowed=Decimal("75"),
        )

        suggestion = SettlementSuggestionService.suggest_for_contact(balance)

        assert suggestion is not None
        assert suggestion.from_contact_id is None  # Owner pays
        assert suggestion.to_contact_id == contact_id  # To contact
        assert suggestion.amount == Decimal("75")

    def test_suggest_for_zero_balance(self):
        """Test no suggestion for zero balance."""
        balance = ContactBalance(
            contact_id=uuid4(),
            currency_code="USD",
            total_lent=Decimal("50"),
            total_borrowed=Decimal("50"),
        )

        suggestion = SettlementSuggestionService.suggest_for_contact(balance)

        assert suggestion is None

    def test_suggest_all(self):
        """Test suggestions for multiple contacts."""
        contact1 = uuid4()
        contact2 = uuid4()
        balances = {
            contact1: ContactBalance(
                contact_id=contact1,
                currency_code="USD",
                total_lent=Decimal("100"),
                total_borrowed=Decimal("0"),
            ),
            contact2: ContactBalance(
                contact_id=contact2,
                currency_code="USD",
                total_lent=Decimal("0"),
                total_borrowed=Decimal("50"),
            ),
        }

        suggestions = SettlementSuggestionService.suggest_all(balances)

        assert len(suggestions) == 2
