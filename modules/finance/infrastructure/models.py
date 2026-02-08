"""Django ORM models for the finance module.

These models handle persistence. Business logic is in the domain layer.
All tenant-scoped models include tenant_id for data isolation.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TenantScopedManager(models.Manager):
    """Manager that scopes queries to a tenant."""

    def for_tenant(self, tenant_id: uuid.UUID) -> models.QuerySet:
        """Filter queryset by tenant ID."""
        return self.get_queryset().filter(tenant_id=tenant_id)


class TenantScopedModel(models.Model):
    """Abstract base model with tenant scoping.

    All finance models inherit from this to ensure tenant isolation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


# =============================================================================
# Category Model
# =============================================================================


class Category(TenantScopedModel):
    """Transaction category for classification."""

    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    icon = models.CharField(max_length=50, blank=True, null=True)
    color = models.CharField(max_length=7, blank=True, null=True)
    is_system = models.BooleanField(default=False)
    is_income = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "name"],
                name="unique_category_name_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        return self.name


# =============================================================================
# Account Model
# =============================================================================


class Account(TenantScopedModel):
    """Financial account (bank, wallet, cash, etc.)."""

    class AccountType(models.TextChoices):
        CHECKING = "checking", "Checking"
        SAVINGS = "savings", "Savings"
        CASH = "cash", "Cash"
        CREDIT_CARD = "credit_card", "Credit Card"
        INVESTMENT = "investment", "Investment"
        WALLET = "wallet", "Wallet"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        CLOSED = "closed", "Closed"

    name = models.CharField(max_length=100)
    account_type = models.CharField(
        max_length=20,
        choices=AccountType.choices,
        default=AccountType.CHECKING,
    )
    currency_code = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    institution = models.CharField(max_length=100, blank=True, null=True)
    account_number_masked = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_included_in_net_worth = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ["display_order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "name"],
                name="unique_account_name_per_tenant",
            ),
        ]
        permissions = [
            ("export_accounts", "Can export account data"),
            ("view_account_analytics", "Can view account analytics"),
            ("bulk_import_accounts", "Can bulk import accounts"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.account_type})"

    def calculate_balance(self) -> Decimal:
        """Calculate balance from posted transactions."""
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from decimal import Decimal

        transactions = self.transactions.filter(status=Transaction.Status.POSTED)
        credits = transactions.filter(
            transaction_type=Transaction.TransactionType.CREDIT
        ).aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]
        debits = transactions.filter(
            transaction_type=Transaction.TransactionType.DEBIT
        ).aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]
        return credits - debits


# =============================================================================
# Transaction Model
# =============================================================================


class Transaction(TenantScopedModel):
    """Financial transaction (credit or debit)."""

    class TransactionType(models.TextChoices):
        CREDIT = "credit", "Credit (Money In)"
        DEBIT = "debit", "Debit (Money Out)"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        POSTED = "posted", "Posted"
        VOIDED = "voided", "Voided"

    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionType.choices,
    )
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    currency_code = models.CharField(max_length=3, default="USD")
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    transaction_date = models.DateField()
    posted_at = models.DateTimeField(blank=True, null=True)
    description = models.CharField(max_length=500, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    idempotency_key = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    adjustment_for = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="adjustments",
    )
    exchange_rate = models.DecimalField(
        max_digits=19, decimal_places=10, blank=True, null=True
    )

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-transaction_date", "-created_at"]
        indexes = [
            models.Index(fields=["tenant_id", "account", "transaction_date"]),
            models.Index(fields=["tenant_id", "category"]),
            models.Index(fields=["tenant_id", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "idempotency_key"],
                name="unique_idempotency_key_per_tenant",
                condition=models.Q(idempotency_key__isnull=False),
            ),
        ]
        permissions = [
            ("bulk_import_transactions", "Can bulk import transactions"),
            ("export_transactions", "Can export transactions"),
            ("view_transaction_analytics", "Can view transaction analytics"),
        ]

    def __str__(self) -> str:
        sign = "+" if self.transaction_type == self.TransactionType.CREDIT else "-"
        return f"{sign}{self.amount} {self.currency_code} on {self.transaction_date}"


# =============================================================================
# Transfer Model
# =============================================================================


class Transfer(TenantScopedModel):
    """Transfer between two accounts."""

    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="outgoing_transfers",
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="incoming_transfers",
    )
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    currency_code = models.CharField(max_length=3, default="USD")
    from_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    to_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    transfer_date = models.DateField()
    description = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True, null=True)
    exchange_rate = models.DecimalField(
        max_digits=19, decimal_places=10, blank=True, null=True
    )

    class Meta:
        verbose_name = "Transfer"
        verbose_name_plural = "Transfers"
        ordering = ["-transfer_date", "-created_at"]

    def __str__(self) -> str:
        return f"Transfer {self.amount} from {self.from_account} to {self.to_account}"


# =============================================================================
# Asset Model
# =============================================================================


class Asset(TenantScopedModel):
    """Asset (something of value owned)."""

    class AssetType(models.TextChoices):
        REAL_ESTATE = "real_estate", "Real Estate"
        VEHICLE = "vehicle", "Vehicle"
        INVESTMENT = "investment", "Investment"
        COLLECTIBLE = "collectible", "Collectible"
        RECEIVABLE = "receivable", "Receivable"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    asset_type = models.CharField(
        max_length=20,
        choices=AssetType.choices,
        default=AssetType.OTHER,
    )
    current_value = models.DecimalField(max_digits=19, decimal_places=4)
    currency_code = models.CharField(max_length=3, default="USD")
    purchase_date = models.DateField(blank=True, null=True)
    purchase_price = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_included_in_net_worth = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.current_value} {self.currency_code})"


# =============================================================================
# Liability Model
# =============================================================================


class Liability(TenantScopedModel):
    """Liability (money owed)."""

    class LiabilityType(models.TextChoices):
        MORTGAGE = "mortgage", "Mortgage"
        AUTO_LOAN = "auto_loan", "Auto Loan"
        PERSONAL_LOAN = "personal_loan", "Personal Loan"
        STUDENT_LOAN = "student_loan", "Student Loan"
        CREDIT_CARD = "credit_card", "Credit Card"
        LINE_OF_CREDIT = "line_of_credit", "Line of Credit"
        OTHER = "other", "Other"

    name = models.CharField(max_length=200)
    liability_type = models.CharField(
        max_length=20,
        choices=LiabilityType.choices,
        default=LiabilityType.OTHER,
    )
    current_balance = models.DecimalField(max_digits=19, decimal_places=4)
    currency_code = models.CharField(max_length=3, default="USD")
    interest_rate = models.DecimalField(
        max_digits=6, decimal_places=4, blank=True, null=True
    )
    minimum_payment = models.DecimalField(
        max_digits=19, decimal_places=4, blank=True, null=True
    )
    due_day = models.PositiveSmallIntegerField(blank=True, null=True)
    creditor = models.CharField(max_length=100, blank=True, null=True)
    account_number_masked = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_included_in_net_worth = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Liability"
        verbose_name_plural = "Liabilities"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.current_balance} {self.currency_code})"


# =============================================================================
# Loan Model
# =============================================================================


class Loan(TenantScopedModel):
    """Loan with repayment schedule."""

    class LoanStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        PAID_OFF = "paid_off", "Paid Off"
        DEFAULTED = "defaulted", "Defaulted"
        DEFERRED = "deferred", "Deferred"

    class PaymentFrequency(models.TextChoices):
        WEEKLY = "weekly", "Weekly"
        BIWEEKLY = "biweekly", "Bi-Weekly"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        ANNUALLY = "annually", "Annually"

    name = models.CharField(max_length=200)
    liability_type = models.CharField(
        max_length=20,
        choices=Liability.LiabilityType.choices,
        default=Liability.LiabilityType.PERSONAL_LOAN,
    )
    original_principal = models.DecimalField(max_digits=19, decimal_places=4)
    current_balance = models.DecimalField(max_digits=19, decimal_places=4)
    currency_code = models.CharField(max_length=3, default="USD")
    interest_rate = models.DecimalField(max_digits=6, decimal_places=4)
    payment_amount = models.DecimalField(max_digits=19, decimal_places=4)
    payment_frequency = models.CharField(
        max_length=15,
        choices=PaymentFrequency.choices,
        default=PaymentFrequency.MONTHLY,
    )
    status = models.CharField(
        max_length=15,
        choices=LoanStatus.choices,
        default=LoanStatus.ACTIVE,
    )
    start_date = models.DateField(blank=True, null=True)
    expected_payoff_date = models.DateField(blank=True, null=True)
    next_payment_date = models.DateField(blank=True, null=True)
    lender = models.CharField(max_length=100, blank=True, null=True)
    account_number_masked = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    linked_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_loans",
    )
    is_included_in_net_worth = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Loan"
        verbose_name_plural = "Loans"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.current_balance}/{self.original_principal} {self.currency_code})"


# =============================================================================
# Idempotency Key Tracking
# =============================================================================


class IdempotencyKey(models.Model):
    """Tracks idempotency keys for exactly-once processing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    key = models.CharField(max_length=255)
    resource_id = models.UUIDField()
    resource_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = "Idempotency Key"
        verbose_name_plural = "Idempotency Keys"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant_id", "key"],
                name="unique_idempotency_key",
            ),
        ]
        indexes = [
            models.Index(fields=["tenant_id", "key"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.key} -> {self.resource_type}:{self.resource_id}"


# =============================================================================
# Exchange Rate History
# =============================================================================


class ExchangeRate(models.Model):
    """Historical exchange rates for multi-currency support."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=19, decimal_places=10)
    effective_date = models.DateField()
    source = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Exchange Rate"
        verbose_name_plural = "Exchange Rates"
        ordering = ["-effective_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_currency", "to_currency", "effective_date"],
                name="unique_exchange_rate_per_day",
            ),
        ]
        indexes = [
            models.Index(fields=["from_currency", "to_currency", "effective_date"]),
        ]

    def __str__(self) -> str:
        return f"1 {self.from_currency} = {self.rate} {self.to_currency} on {self.effective_date}"
