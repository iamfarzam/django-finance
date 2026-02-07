"""Unit tests for finance domain entities."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from modules.finance.domain.entities import (
    Account,
    Asset,
    Category,
    Liability,
    Loan,
    Transaction,
    Transfer,
)
from modules.finance.domain.enums import (
    AccountStatus,
    AccountType,
    AssetType,
    LiabilityType,
    LoanStatus,
    PaymentFrequency,
    TransactionStatus,
    TransactionType,
)


class TestAccount:
    """Tests for Account entity."""

    def test_create_account(self):
        """Test creating an account."""
        tenant_id = uuid4()
        account = Account.create(
            tenant_id=tenant_id,
            name="Checking Account",
            account_type=AccountType.CHECKING,
            currency_code="USD",
        )
        assert account.name == "Checking Account"
        assert account.account_type == AccountType.CHECKING
        assert account.currency_code == "USD"
        assert account.tenant_id == tenant_id
        assert account.status == AccountStatus.ACTIVE
        assert account.is_active
        assert not account.is_closed

    def test_account_with_institution(self):
        """Test creating account with institution."""
        account = Account.create(
            tenant_id=uuid4(),
            name="Savings",
            account_type=AccountType.SAVINGS,
            currency_code="EUR",
            institution="Bank of Europe",
        )
        assert account.institution == "Bank of Europe"

    def test_close_account(self):
        """Test closing an account."""
        account = Account.create(
            tenant_id=uuid4(),
            name="Test",
            account_type=AccountType.CHECKING,
            currency_code="USD",
        )
        account.close()
        assert account.status == AccountStatus.CLOSED
        assert account.is_closed
        assert not account.is_active

    def test_reopen_account(self):
        """Test reopening a closed account."""
        account = Account.create(
            tenant_id=uuid4(),
            name="Test",
            account_type=AccountType.CHECKING,
            currency_code="USD",
        )
        account.close()
        account.reopen()
        assert account.is_active
        assert not account.is_closed

    def test_unsupported_currency_raises(self):
        """Test that unsupported currency raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported currency"):
            Account.create(
                tenant_id=uuid4(),
                name="Test",
                account_type=AccountType.CHECKING,
                currency_code="XYZ",
            )


class TestTransaction:
    """Tests for Transaction entity."""

    def test_create_credit_transaction(self):
        """Test creating a credit (money in) transaction."""
        tenant_id = uuid4()
        account_id = uuid4()
        tx = Transaction.create_credit(
            tenant_id=tenant_id,
            account_id=account_id,
            amount=Decimal("100.00"),
            currency_code="USD",
            description="Salary",
        )
        assert tx.transaction_type == TransactionType.CREDIT
        assert tx.amount == Decimal("100.00")
        assert tx.description == "Salary"
        assert tx.status == TransactionStatus.PENDING
        assert tx.is_pending
        assert tx.signed_amount == Decimal("100.00")

    def test_create_debit_transaction(self):
        """Test creating a debit (money out) transaction."""
        tx = Transaction.create_debit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("50.00"),
            currency_code="USD",
            description="Groceries",
        )
        assert tx.transaction_type == TransactionType.DEBIT
        assert tx.signed_amount == Decimal("-50.00")

    def test_post_transaction(self):
        """Test posting a transaction."""
        tx = Transaction.create_credit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("100"),
            currency_code="USD",
        )
        tx.post()
        assert tx.is_posted
        assert tx.posted_at is not None

    def test_void_transaction(self):
        """Test voiding a transaction."""
        tx = Transaction.create_credit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("100"),
            currency_code="USD",
        )
        tx.void()
        assert tx.is_voided

    def test_void_already_voided_raises(self):
        """Test that voiding already voided transaction raises."""
        tx = Transaction.create_credit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("100"),
            currency_code="USD",
        )
        tx.void()
        with pytest.raises(ValueError, match="already voided"):
            tx.void()

    def test_post_non_pending_raises(self):
        """Test that posting non-pending transaction raises."""
        tx = Transaction.create_credit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("100"),
            currency_code="USD",
        )
        tx.post()
        with pytest.raises(ValueError, match="Cannot post"):
            tx.post()

    def test_negative_amount_raises(self):
        """Test that negative amount raises ValueError."""
        with pytest.raises(ValueError, match="must be non-negative"):
            Transaction(
                id=uuid4(),
                tenant_id=uuid4(),
                account_id=uuid4(),
                transaction_type=TransactionType.CREDIT,
                amount=Decimal("-100"),
                currency_code="USD",
            )

    def test_create_adjustment(self):
        """Test creating an adjustment transaction."""
        original = Transaction.create_credit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("100"),
            currency_code="USD",
        )
        adjustment = original.create_adjustment(
            new_amount=Decimal("150"),
            notes="Corrected amount",
        )
        assert adjustment.is_adjustment
        assert adjustment.adjustment_for_id == original.id
        assert adjustment.amount == Decimal("150")

    def test_transaction_with_category(self):
        """Test transaction with category."""
        category_id = uuid4()
        tx = Transaction.create_debit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("50"),
            currency_code="USD",
            category_id=category_id,
        )
        assert tx.category_id == category_id

    def test_money_property(self):
        """Test Money property conversion."""
        tx = Transaction.create_credit(
            tenant_id=uuid4(),
            account_id=uuid4(),
            amount=Decimal("99.99"),
            currency_code="USD",
        )
        money = tx.money
        assert money.amount == Decimal("99.99")
        assert money.currency.code == "USD"


class TestTransfer:
    """Tests for Transfer entity."""

    def test_create_transfer(self):
        """Test creating a transfer."""
        transfer = Transfer.create(
            tenant_id=uuid4(),
            from_account_id=uuid4(),
            to_account_id=uuid4(),
            amount=Decimal("500"),
            currency_code="USD",
            description="Savings transfer",
        )
        assert transfer.amount == Decimal("500")
        assert transfer.description == "Savings transfer"

    def test_same_account_transfer_raises(self):
        """Test that transfer to same account raises."""
        account_id = uuid4()
        with pytest.raises(ValueError, match="same account"):
            Transfer.create(
                tenant_id=uuid4(),
                from_account_id=account_id,
                to_account_id=account_id,
                amount=Decimal("100"),
                currency_code="USD",
            )

    def test_create_transactions(self):
        """Test creating linked transactions."""
        transfer = Transfer.create(
            tenant_id=uuid4(),
            from_account_id=uuid4(),
            to_account_id=uuid4(),
            amount=Decimal("100"),
            currency_code="USD",
        )
        debit, credit = transfer.create_transactions()
        assert debit.transaction_type == TransactionType.DEBIT
        assert credit.transaction_type == TransactionType.CREDIT
        assert debit.amount == Decimal("100")
        assert credit.amount == Decimal("100")


class TestAsset:
    """Tests for Asset entity."""

    def test_create_asset(self):
        """Test creating an asset."""
        asset = Asset.create(
            tenant_id=uuid4(),
            name="Investment Portfolio",
            asset_type=AssetType.INVESTMENT,
            current_value=Decimal("50000"),
            currency_code="USD",
        )
        assert asset.name == "Investment Portfolio"
        assert asset.current_value == Decimal("50000")

    def test_asset_gain_loss(self):
        """Test calculating asset gain/loss."""
        asset = Asset.create(
            tenant_id=uuid4(),
            name="Stock",
            asset_type=AssetType.INVESTMENT,
            current_value=Decimal("1500"),
            currency_code="USD",
            purchase_price=Decimal("1000"),
        )
        gain = asset.gain_loss
        assert gain is not None
        assert gain.amount == Decimal("500")

    def test_asset_no_gain_loss_without_purchase_price(self):
        """Test that gain_loss is None without purchase price."""
        asset = Asset.create(
            tenant_id=uuid4(),
            name="Art",
            asset_type=AssetType.COLLECTIBLE,
            current_value=Decimal("5000"),
            currency_code="USD",
        )
        assert asset.gain_loss is None

    def test_update_asset_value(self):
        """Test updating asset value."""
        asset = Asset.create(
            tenant_id=uuid4(),
            name="Property",
            asset_type=AssetType.REAL_ESTATE,
            current_value=Decimal("200000"),
            currency_code="USD",
        )
        asset.update_value(Decimal("210000"))
        assert asset.current_value == Decimal("210000")


class TestLiability:
    """Tests for Liability entity."""

    def test_create_liability(self):
        """Test creating a liability."""
        liability = Liability.create(
            tenant_id=uuid4(),
            name="Credit Card",
            liability_type=LiabilityType.CREDIT_CARD,
            current_balance=Decimal("5000"),
            currency_code="USD",
        )
        assert liability.name == "Credit Card"
        assert liability.current_balance == Decimal("5000")

    def test_record_payment(self):
        """Test recording a payment on liability."""
        liability = Liability.create(
            tenant_id=uuid4(),
            name="Credit Card",
            liability_type=LiabilityType.CREDIT_CARD,
            current_balance=Decimal("5000"),
            currency_code="USD",
        )
        liability.record_payment(Decimal("1000"))
        assert liability.current_balance == Decimal("4000")

    def test_payment_cannot_go_negative(self):
        """Test that payment cannot make balance negative."""
        liability = Liability.create(
            tenant_id=uuid4(),
            name="Credit Card",
            liability_type=LiabilityType.CREDIT_CARD,
            current_balance=Decimal("100"),
            currency_code="USD",
        )
        liability.record_payment(Decimal("200"))
        assert liability.current_balance == Decimal("0")


class TestLoan:
    """Tests for Loan entity."""

    def test_create_loan(self):
        """Test creating a loan."""
        loan = Loan.create(
            tenant_id=uuid4(),
            name="Auto Loan",
            liability_type=LiabilityType.AUTO_LOAN,
            principal=Decimal("25000"),
            currency_code="USD",
            interest_rate=Decimal("5.5"),
            payment_amount=Decimal("500"),
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        assert loan.original_principal == Decimal("25000")
        assert loan.current_balance == Decimal("25000")
        assert loan.is_active
        assert not loan.is_paid_off

    def test_record_loan_payment(self):
        """Test recording a loan payment."""
        loan = Loan.create(
            tenant_id=uuid4(),
            name="Personal Loan",
            liability_type=LiabilityType.PERSONAL_LOAN,
            principal=Decimal("10000"),
            currency_code="USD",
            interest_rate=Decimal("8"),
            payment_amount=Decimal("300"),
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        loan.record_payment(Decimal("500"))
        assert loan.current_balance == Decimal("9500")
        assert loan.principal_paid == Decimal("500")

    def test_loan_paid_off(self):
        """Test that loan is marked paid off when balance is zero."""
        loan = Loan.create(
            tenant_id=uuid4(),
            name="Small Loan",
            liability_type=LiabilityType.PERSONAL_LOAN,
            principal=Decimal("1000"),
            currency_code="USD",
            interest_rate=Decimal("5"),
            payment_amount=Decimal("500"),
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        loan.record_payment(Decimal("1000"))
        assert loan.is_paid_off
        assert loan.current_balance == Decimal("0")

    def test_cannot_pay_paid_off_loan(self):
        """Test that paying paid off loan raises."""
        loan = Loan.create(
            tenant_id=uuid4(),
            name="Paid Loan",
            liability_type=LiabilityType.PERSONAL_LOAN,
            principal=Decimal("100"),
            currency_code="USD",
            interest_rate=Decimal("5"),
            payment_amount=Decimal("100"),
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        loan.record_payment(Decimal("100"))
        with pytest.raises(ValueError, match="paid-off"):
            loan.record_payment(Decimal("50"))

    def test_principal_paid_percentage(self):
        """Test calculating principal paid percentage."""
        loan = Loan.create(
            tenant_id=uuid4(),
            name="Test Loan",
            liability_type=LiabilityType.PERSONAL_LOAN,
            principal=Decimal("1000"),
            currency_code="USD",
            interest_rate=Decimal("5"),
            payment_amount=Decimal("100"),
            payment_frequency=PaymentFrequency.MONTHLY,
        )
        loan.record_payment(Decimal("250"))
        assert loan.principal_paid_percentage == Decimal("25")


class TestCategory:
    """Tests for Category entity."""

    def test_create_category(self):
        """Test creating a category."""
        category = Category.create(
            tenant_id=uuid4(),
            name="Groceries",
            is_income=False,
        )
        assert category.name == "Groceries"
        assert not category.is_income
        assert not category.is_system

    def test_create_income_category(self):
        """Test creating an income category."""
        category = Category.create(
            tenant_id=uuid4(),
            name="Salary",
            is_income=True,
        )
        assert category.is_income

    def test_category_with_parent(self):
        """Test creating a subcategory."""
        parent_id = uuid4()
        category = Category.create(
            tenant_id=uuid4(),
            name="Fast Food",
            parent_id=parent_id,
        )
        assert category.parent_id == parent_id
