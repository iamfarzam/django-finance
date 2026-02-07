"""Unit tests for finance domain services."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from modules.finance.domain.entities import Account, Asset, Liability, Loan, Transaction
from modules.finance.domain.enums import (
    AccountStatus,
    AccountType,
    AssetType,
    LiabilityType,
    PaymentFrequency,
    TransactionStatus,
    TransactionType,
)
from modules.finance.domain.services import (
    AccountLimitChecker,
    BalanceCalculator,
    CashFlowAnalyzer,
    NetWorthCalculator,
    TransactionValidator,
)
from modules.finance.domain.value_objects import Money


class TestBalanceCalculator:
    """Tests for BalanceCalculator service."""

    def test_calculate_balance_empty(self):
        """Test balance calculation with no transactions."""
        result = BalanceCalculator.calculate([], "USD")
        assert result.balance.amount == Decimal("0")
        assert result.transaction_count == 0

    def test_calculate_balance_credits_only(self):
        """Test balance with only credits."""
        tenant_id = uuid4()
        account_id = uuid4()
        transactions = [
            self._create_posted_credit(tenant_id, account_id, Decimal("100")),
            self._create_posted_credit(tenant_id, account_id, Decimal("50")),
        ]
        result = BalanceCalculator.calculate(transactions, "USD")
        assert result.balance.amount == Decimal("150")
        assert result.total_credits.amount == Decimal("150")
        assert result.total_debits.amount == Decimal("0")
        assert result.transaction_count == 2

    def test_calculate_balance_debits_only(self):
        """Test balance with only debits."""
        tenant_id = uuid4()
        account_id = uuid4()
        transactions = [
            self._create_posted_debit(tenant_id, account_id, Decimal("75")),
        ]
        result = BalanceCalculator.calculate(transactions, "USD")
        assert result.balance.amount == Decimal("-75")
        assert result.total_debits.amount == Decimal("75")

    def test_calculate_balance_mixed(self):
        """Test balance with credits and debits."""
        tenant_id = uuid4()
        account_id = uuid4()
        transactions = [
            self._create_posted_credit(tenant_id, account_id, Decimal("1000")),
            self._create_posted_debit(tenant_id, account_id, Decimal("250")),
            self._create_posted_debit(tenant_id, account_id, Decimal("150")),
        ]
        result = BalanceCalculator.calculate(transactions, "USD")
        assert result.balance.amount == Decimal("600")  # 1000 - 250 - 150

    def test_excludes_voided_transactions(self):
        """Test that voided transactions are excluded."""
        tenant_id = uuid4()
        account_id = uuid4()
        credit = self._create_posted_credit(tenant_id, account_id, Decimal("100"))
        voided = self._create_posted_credit(tenant_id, account_id, Decimal("999"))
        voided.void()

        result = BalanceCalculator.calculate([credit, voided], "USD")
        assert result.balance.amount == Decimal("100")
        assert result.transaction_count == 1

    def test_excludes_pending_by_default(self):
        """Test that pending transactions are excluded by default."""
        tenant_id = uuid4()
        account_id = uuid4()
        posted = self._create_posted_credit(tenant_id, account_id, Decimal("100"))
        pending = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("500"),
            currency_code="USD",
        )  # Not posted

        result = BalanceCalculator.calculate([posted, pending], "USD")
        assert result.balance.amount == Decimal("100")

    def test_includes_pending_when_requested(self):
        """Test including pending transactions when requested."""
        tenant_id = uuid4()
        account_id = uuid4()
        posted = self._create_posted_credit(tenant_id, account_id, Decimal("100"))
        pending = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("500"),
            currency_code="USD",
        )

        result = BalanceCalculator.calculate(
            [posted, pending], "USD", include_pending=True
        )
        assert result.balance.amount == Decimal("600")

    def test_as_of_date_filter(self):
        """Test filtering by as_of_date."""
        tenant_id = uuid4()
        account_id = uuid4()
        old_tx = self._create_posted_credit(tenant_id, account_id, Decimal("100"))
        old_tx.transaction_date = date(2024, 1, 1)

        new_tx = self._create_posted_credit(tenant_id, account_id, Decimal("200"))
        new_tx.transaction_date = date(2024, 6, 1)

        result = BalanceCalculator.calculate(
            [old_tx, new_tx], "USD", as_of_date=date(2024, 3, 1)
        )
        assert result.balance.amount == Decimal("100")

    def _create_posted_credit(self, tenant_id, account_id, amount):
        tx = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=amount,
            currency_code="USD",
        )
        tx.post()
        return tx

    def _create_posted_debit(self, tenant_id, account_id, amount):
        tx = Transaction.create_debit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=amount,
            currency_code="USD",
        )
        tx.post()
        return tx


class TestTransactionValidator:
    """Tests for TransactionValidator service."""

    def test_validate_valid_amount(self):
        """Test validating a valid amount."""
        errors = TransactionValidator.validate_amount(Decimal("100.00"))
        assert errors == []

    def test_validate_negative_amount(self):
        """Test validating negative amount."""
        errors = TransactionValidator.validate_amount(Decimal("-50"))
        assert "cannot be negative" in errors[0]

    def test_validate_zero_amount(self):
        """Test validating zero amount."""
        errors = TransactionValidator.validate_amount(Decimal("0"))
        assert "cannot be zero" in errors[0]

    def test_validate_excessive_precision(self):
        """Test validating amount with too many decimal places."""
        errors = TransactionValidator.validate_amount(Decimal("1.123456789"))
        assert "too many decimal places" in errors[0]

    def test_validate_valid_date(self):
        """Test validating a valid date."""
        errors = TransactionValidator.validate_date(date.today())
        assert errors == []

    def test_validate_future_date_one_year(self):
        """Test validating date slightly in the future is OK."""
        from datetime import timedelta
        future = date.today() + timedelta(days=100)
        errors = TransactionValidator.validate_date(future)
        assert errors == []

    def test_validate_too_far_future(self):
        """Test validating date too far in future."""
        from datetime import timedelta
        far_future = date.today() + timedelta(days=400)
        errors = TransactionValidator.validate_date(far_future)
        assert "too far in the future" in errors[0]

    def test_validate_too_old(self):
        """Test validating date too far in past."""
        old_date = date(2010, 1, 1)
        errors = TransactionValidator.validate_date(old_date)
        assert "too far in the past" in errors[0]


class TestAccountLimitChecker:
    """Tests for AccountLimitChecker service."""

    def test_user_within_limit(self):
        """Test user role within limit."""
        can_create, limit = AccountLimitChecker.check_limit("user", 2)
        assert can_create
        assert limit == 3

    def test_user_at_limit(self):
        """Test user role at limit."""
        can_create, limit = AccountLimitChecker.check_limit("user", 3)
        assert not can_create
        assert limit == 3

    def test_premium_unlimited(self):
        """Test premium role is unlimited."""
        can_create, limit = AccountLimitChecker.check_limit("premium", 100)
        assert can_create
        assert limit == -1  # -1 indicates unlimited

    def test_superadmin_unlimited(self):
        """Test superadmin role is unlimited."""
        can_create, limit = AccountLimitChecker.check_limit("superadmin", 1000)
        assert can_create

    def test_unknown_role_defaults_to_user(self):
        """Test unknown role defaults to user limit."""
        can_create, limit = AccountLimitChecker.check_limit("unknown", 2)
        assert can_create
        assert limit == 3


class TestNetWorthCalculator:
    """Tests for NetWorthCalculator service."""

    def test_calculate_net_worth_empty(self):
        """Test net worth with no data."""
        result = NetWorthCalculator.calculate(
            accounts=[],
            assets=[],
            liabilities=[],
            loans=[],
            base_currency="USD",
        )
        assert result.net_worth.amount == Decimal("0")
        assert result.account_count == 0

    def test_calculate_net_worth_assets_only(self):
        """Test net worth with only assets."""
        asset = Asset.create(
            tenant_id=uuid4(),
            name="Investment",
            asset_type=AssetType.INVESTMENT,
            current_value=Decimal("10000"),
            currency_code="USD",
        )
        result = NetWorthCalculator.calculate(
            accounts=[],
            assets=[asset],
            liabilities=[],
            loans=[],
            base_currency="USD",
        )
        assert result.total_assets.amount == Decimal("10000")
        assert result.net_worth.amount == Decimal("10000")
        assert result.asset_count == 1

    def test_calculate_net_worth_with_liabilities(self):
        """Test net worth with assets and liabilities."""
        asset = Asset.create(
            tenant_id=uuid4(),
            name="House",
            asset_type=AssetType.REAL_ESTATE,
            current_value=Decimal("300000"),
            currency_code="USD",
        )
        liability = Liability.create(
            tenant_id=uuid4(),
            name="Mortgage",
            liability_type=LiabilityType.MORTGAGE,
            current_balance=Decimal("200000"),
            currency_code="USD",
        )
        result = NetWorthCalculator.calculate(
            accounts=[],
            assets=[asset],
            liabilities=[liability],
            loans=[],
            base_currency="USD",
        )
        assert result.net_worth.amount == Decimal("100000")  # 300k - 200k

    def test_calculate_net_worth_excludes_non_included(self):
        """Test that items not included in net worth are excluded."""
        included_asset = Asset.create(
            tenant_id=uuid4(),
            name="Included",
            asset_type=AssetType.INVESTMENT,
            current_value=Decimal("5000"),
            currency_code="USD",
        )
        excluded_asset = Asset.create(
            tenant_id=uuid4(),
            name="Excluded",
            asset_type=AssetType.COLLECTIBLE,
            current_value=Decimal("10000"),
            currency_code="USD",
        )
        excluded_asset.is_included_in_net_worth = False

        result = NetWorthCalculator.calculate(
            accounts=[],
            assets=[included_asset, excluded_asset],
            liabilities=[],
            loans=[],
            base_currency="USD",
        )
        assert result.total_assets.amount == Decimal("5000")
        assert result.asset_count == 1


class TestCashFlowAnalyzer:
    """Tests for CashFlowAnalyzer service."""

    def test_analyze_empty(self):
        """Test cash flow with no transactions."""
        result = CashFlowAnalyzer.analyze(
            transactions=[],
            category_names={},
            currency_code="USD",
        )
        assert result.total_income.amount == Decimal("0")
        assert result.total_expenses.amount == Decimal("0")
        assert result.net_cash_flow.amount == Decimal("0")

    def test_analyze_income_only(self):
        """Test cash flow with only income."""
        tenant_id = uuid4()
        account_id = uuid4()
        category_id = uuid4()

        tx = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("1000"),
            currency_code="USD",
            category_id=category_id,
        )
        tx.post()

        result = CashFlowAnalyzer.analyze(
            transactions=[tx],
            category_names={str(category_id): "Salary"},
            currency_code="USD",
        )
        assert result.total_income.amount == Decimal("1000")
        assert result.total_expenses.amount == Decimal("0")
        assert result.net_cash_flow.amount == Decimal("1000")
        assert "Salary" in result.income_by_category

    def test_analyze_mixed(self):
        """Test cash flow with income and expenses."""
        tenant_id = uuid4()
        account_id = uuid4()

        income = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("3000"),
            currency_code="USD",
        )
        income.post()

        expense = Transaction.create_debit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("1500"),
            currency_code="USD",
        )
        expense.post()

        result = CashFlowAnalyzer.analyze(
            transactions=[income, expense],
            category_names={},
            currency_code="USD",
        )
        assert result.total_income.amount == Decimal("3000")
        assert result.total_expenses.amount == Decimal("1500")
        assert result.net_cash_flow.amount == Decimal("1500")

    def test_analyze_date_filter(self):
        """Test cash flow with date filtering."""
        tenant_id = uuid4()
        account_id = uuid4()

        jan_income = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("1000"),
            currency_code="USD",
            transaction_date=date(2024, 1, 15),
        )
        jan_income.post()

        feb_income = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("2000"),
            currency_code="USD",
            transaction_date=date(2024, 2, 15),
        )
        feb_income.post()

        result = CashFlowAnalyzer.analyze(
            transactions=[jan_income, feb_income],
            category_names={},
            currency_code="USD",
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 28),
        )
        assert result.total_income.amount == Decimal("2000")

    def test_analyze_excludes_pending(self):
        """Test that pending transactions are excluded."""
        tenant_id = uuid4()
        account_id = uuid4()

        posted = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("1000"),
            currency_code="USD",
        )
        posted.post()

        pending = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("5000"),
            currency_code="USD",
        )
        # Not posted

        result = CashFlowAnalyzer.analyze(
            transactions=[posted, pending],
            category_names={},
            currency_code="USD",
        )
        assert result.total_income.amount == Decimal("1000")
