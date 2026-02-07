"""Domain entities for the finance module.

Entities are objects with identity that persist over time.
They contain business logic and validation rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

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
from modules.finance.domain.value_objects import Currency, Money

if TYPE_CHECKING:
    pass


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


@dataclass
class Category:
    """Transaction category for classification.

    Categories can be system-defined or user-created.
    They help organize transactions for reporting.
    """

    id: UUID
    tenant_id: UUID
    name: str
    parent_id: UUID | None = None
    icon: str | None = None
    color: str | None = None
    is_system: bool = False
    is_income: bool = False
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        *,
        parent_id: UUID | None = None,
        icon: str | None = None,
        color: str | None = None,
        is_income: bool = False,
    ) -> "Category":
        """Create a new user-defined category."""
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            parent_id=parent_id,
            icon=icon,
            color=color,
            is_system=False,
            is_income=is_income,
        )


@dataclass
class Account:
    """Financial account entity.

    Represents a bank account, wallet, cash, credit card, etc.
    Balance is calculated from transactions, not stored directly.
    """

    id: UUID
    tenant_id: UUID
    name: str
    account_type: AccountType
    currency_code: str
    status: AccountStatus = AccountStatus.ACTIVE
    institution: str | None = None
    account_number_masked: str | None = None
    notes: str | None = None
    is_included_in_net_worth: bool = True
    display_order: int = 0
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        account_type: AccountType,
        currency_code: str,
        *,
        institution: str | None = None,
        account_number_masked: str | None = None,
        notes: str | None = None,
    ) -> "Account":
        """Create a new account.

        Args:
            tenant_id: The tenant this account belongs to.
            name: Display name for the account.
            account_type: Type of account.
            currency_code: ISO 4217 currency code.
            institution: Optional financial institution name.
            account_number_masked: Optional masked account number.
            notes: Optional notes.

        Returns:
            New Account instance.
        """
        # Validate currency is supported
        Currency.get(currency_code)

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            account_type=account_type,
            currency_code=currency_code,
            institution=institution,
            account_number_masked=account_number_masked,
            notes=notes,
        )

    @property
    def is_active(self) -> bool:
        """Check if account is active."""
        return self.status == AccountStatus.ACTIVE

    @property
    def is_closed(self) -> bool:
        """Check if account is closed."""
        return self.status == AccountStatus.CLOSED

    @property
    def currency(self) -> Currency:
        """Get the Currency object for this account."""
        return Currency.get(self.currency_code)

    def close(self) -> None:
        """Close the account."""
        self.status = AccountStatus.CLOSED
        self.updated_at = _utc_now()

    def reopen(self) -> None:
        """Reopen a closed account."""
        self.status = AccountStatus.ACTIVE
        self.updated_at = _utc_now()

    def update_name(self, name: str) -> None:
        """Update account name."""
        self.name = name
        self.updated_at = _utc_now()


@dataclass
class Transaction:
    """Financial transaction entity.

    Represents a single financial movement (credit or debit).
    Transactions are immutable once posted - corrections are
    made via adjustment transactions.

    Attributes:
        id: Unique transaction identifier.
        tenant_id: Tenant this transaction belongs to.
        account_id: Account this transaction affects.
        transaction_type: Credit (money in) or Debit (money out).
        amount: Transaction amount (always positive).
        currency_code: Currency of the transaction.
        status: Transaction status (pending, posted, voided).
        transaction_date: Date the transaction occurred.
        description: Transaction description.
        category_id: Optional category for classification.
        reference_number: Optional external reference.
        notes: Optional notes.
        idempotency_key: Key for exactly-once processing.
        adjustment_for_id: If this is an adjustment, the original transaction ID.
        exchange_rate: Exchange rate if different from account currency.
        created_at: When this record was created.
        updated_at: When this record was last updated.
    """

    id: UUID
    tenant_id: UUID
    account_id: UUID
    transaction_type: TransactionType
    amount: Decimal
    currency_code: str
    status: TransactionStatus = TransactionStatus.PENDING
    transaction_date: date = field(default_factory=lambda: date.today())
    posted_at: datetime | None = None
    description: str = ""
    category_id: UUID | None = None
    reference_number: str | None = None
    notes: str | None = None
    idempotency_key: str | None = None
    adjustment_for_id: UUID | None = None
    exchange_rate: Decimal | None = None
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        """Validate transaction on creation."""
        if self.amount < Decimal("0"):
            raise ValueError("Transaction amount must be non-negative")

    @classmethod
    def create_credit(
        cls,
        tenant_id: UUID,
        account_id: UUID,
        amount: Decimal | int | float | str,
        currency_code: str,
        *,
        description: str = "",
        transaction_date: date | None = None,
        category_id: UUID | None = None,
        reference_number: str | None = None,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> "Transaction":
        """Create a credit (money in) transaction."""
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            account_id=account_id,
            transaction_type=TransactionType.CREDIT,
            amount=Decimal(str(amount)),
            currency_code=currency_code,
            transaction_date=transaction_date or date.today(),
            description=description,
            category_id=category_id,
            reference_number=reference_number,
            notes=notes,
            idempotency_key=idempotency_key,
        )

    @classmethod
    def create_debit(
        cls,
        tenant_id: UUID,
        account_id: UUID,
        amount: Decimal | int | float | str,
        currency_code: str,
        *,
        description: str = "",
        transaction_date: date | None = None,
        category_id: UUID | None = None,
        reference_number: str | None = None,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> "Transaction":
        """Create a debit (money out) transaction."""
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            account_id=account_id,
            transaction_type=TransactionType.DEBIT,
            amount=Decimal(str(amount)),
            currency_code=currency_code,
            transaction_date=transaction_date or date.today(),
            description=description,
            category_id=category_id,
            reference_number=reference_number,
            notes=notes,
            idempotency_key=idempotency_key,
        )

    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == TransactionStatus.PENDING

    @property
    def is_posted(self) -> bool:
        """Check if transaction is posted."""
        return self.status == TransactionStatus.POSTED

    @property
    def is_voided(self) -> bool:
        """Check if transaction is voided."""
        return self.status == TransactionStatus.VOIDED

    @property
    def is_adjustment(self) -> bool:
        """Check if this is an adjustment transaction."""
        return self.adjustment_for_id is not None

    @property
    def signed_amount(self) -> Decimal:
        """Get the signed amount for balance calculations.

        Returns:
            Positive for credits, negative for debits.
        """
        return self.amount * self.transaction_type.sign

    @property
    def money(self) -> Money:
        """Get the transaction amount as a Money value object."""
        return Money.of(self.amount, self.currency_code)

    def post(self) -> None:
        """Post the transaction (make it final).

        Posted transactions are immutable and included in balance calculations.
        """
        if self.status != TransactionStatus.PENDING:
            raise ValueError(f"Cannot post transaction in {self.status} status")
        self.status = TransactionStatus.POSTED
        self.posted_at = _utc_now()
        self.updated_at = _utc_now()

    def void(self) -> None:
        """Void the transaction.

        Voided transactions are excluded from balance calculations.
        """
        if self.status == TransactionStatus.VOIDED:
            raise ValueError("Transaction is already voided")
        self.status = TransactionStatus.VOIDED
        self.updated_at = _utc_now()

    def create_adjustment(
        self,
        new_amount: Decimal | None = None,
        new_type: TransactionType | None = None,
        *,
        notes: str | None = None,
    ) -> "Transaction":
        """Create an adjustment transaction for corrections.

        Instead of modifying the original transaction, we create
        a new transaction that references the original.

        Args:
            new_amount: The corrected amount.
            new_type: The corrected transaction type.
            notes: Notes explaining the adjustment.

        Returns:
            New adjustment Transaction.
        """
        return Transaction(
            id=uuid4(),
            tenant_id=self.tenant_id,
            account_id=self.account_id,
            transaction_type=new_type or self.transaction_type,
            amount=new_amount if new_amount is not None else self.amount,
            currency_code=self.currency_code,
            transaction_date=date.today(),
            description=f"Adjustment for transaction {self.id}",
            category_id=self.category_id,
            notes=notes,
            adjustment_for_id=self.id,
        )


@dataclass
class Asset:
    """Asset entity representing something of value owned.

    Assets can be real estate, vehicles, investments, collectibles, etc.
    """

    id: UUID
    tenant_id: UUID
    name: str
    asset_type: AssetType
    current_value: Decimal
    currency_code: str
    purchase_date: date | None = None
    purchase_price: Decimal | None = None
    description: str | None = None
    notes: str | None = None
    is_included_in_net_worth: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        asset_type: AssetType,
        current_value: Decimal | int | float | str,
        currency_code: str,
        *,
        purchase_date: date | None = None,
        purchase_price: Decimal | int | float | str | None = None,
        description: str | None = None,
        notes: str | None = None,
    ) -> "Asset":
        """Create a new asset."""
        # Validate currency
        Currency.get(currency_code)

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            asset_type=asset_type,
            current_value=Decimal(str(current_value)),
            currency_code=currency_code,
            purchase_date=purchase_date,
            purchase_price=Decimal(str(purchase_price)) if purchase_price else None,
            description=description,
            notes=notes,
        )

    @property
    def money(self) -> Money:
        """Get current value as Money."""
        return Money.of(self.current_value, self.currency_code)

    @property
    def gain_loss(self) -> Money | None:
        """Calculate gain/loss if purchase price is known."""
        if self.purchase_price is None:
            return None
        diff = self.current_value - self.purchase_price
        return Money.of(diff, self.currency_code)

    def update_value(self, new_value: Decimal | int | float | str) -> None:
        """Update the current value of the asset."""
        self.current_value = Decimal(str(new_value))
        self.updated_at = _utc_now()


@dataclass
class Liability:
    """Liability entity representing money owed.

    Liabilities can be mortgages, credit cards, personal loans, etc.
    """

    id: UUID
    tenant_id: UUID
    name: str
    liability_type: LiabilityType
    current_balance: Decimal
    currency_code: str
    interest_rate: Decimal | None = None
    minimum_payment: Decimal | None = None
    due_day: int | None = None
    creditor: str | None = None
    account_number_masked: str | None = None
    notes: str | None = None
    is_included_in_net_worth: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        liability_type: LiabilityType,
        current_balance: Decimal | int | float | str,
        currency_code: str,
        *,
        interest_rate: Decimal | int | float | str | None = None,
        minimum_payment: Decimal | int | float | str | None = None,
        due_day: int | None = None,
        creditor: str | None = None,
        account_number_masked: str | None = None,
        notes: str | None = None,
    ) -> "Liability":
        """Create a new liability."""
        # Validate currency
        Currency.get(currency_code)

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            liability_type=liability_type,
            current_balance=Decimal(str(current_balance)),
            currency_code=currency_code,
            interest_rate=Decimal(str(interest_rate)) if interest_rate else None,
            minimum_payment=Decimal(str(minimum_payment)) if minimum_payment else None,
            due_day=due_day,
            creditor=creditor,
            account_number_masked=account_number_masked,
            notes=notes,
        )

    @property
    def money(self) -> Money:
        """Get current balance as Money."""
        return Money.of(self.current_balance, self.currency_code)

    def update_balance(self, new_balance: Decimal | int | float | str) -> None:
        """Update the current balance."""
        self.current_balance = Decimal(str(new_balance))
        self.updated_at = _utc_now()

    def record_payment(self, amount: Decimal | int | float | str) -> None:
        """Record a payment made on this liability."""
        payment = Decimal(str(amount))
        self.current_balance = max(Decimal("0"), self.current_balance - payment)
        self.updated_at = _utc_now()


@dataclass
class Loan:
    """Loan entity with repayment schedule.

    A specialized liability that tracks loan-specific details
    like principal, payment schedule, and payoff date.
    """

    id: UUID
    tenant_id: UUID
    name: str
    liability_type: LiabilityType
    original_principal: Decimal
    current_balance: Decimal
    currency_code: str
    interest_rate: Decimal
    payment_amount: Decimal
    payment_frequency: PaymentFrequency
    status: LoanStatus = LoanStatus.ACTIVE
    start_date: date | None = None
    expected_payoff_date: date | None = None
    next_payment_date: date | None = None
    lender: str | None = None
    account_number_masked: str | None = None
    notes: str | None = None
    linked_account_id: UUID | None = None
    is_included_in_net_worth: bool = True
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        liability_type: LiabilityType,
        principal: Decimal | int | float | str,
        currency_code: str,
        interest_rate: Decimal | int | float | str,
        payment_amount: Decimal | int | float | str,
        payment_frequency: PaymentFrequency,
        *,
        start_date: date | None = None,
        expected_payoff_date: date | None = None,
        next_payment_date: date | None = None,
        lender: str | None = None,
        account_number_masked: str | None = None,
        notes: str | None = None,
    ) -> "Loan":
        """Create a new loan."""
        # Validate currency
        Currency.get(currency_code)

        principal_decimal = Decimal(str(principal))

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name,
            liability_type=liability_type,
            original_principal=principal_decimal,
            current_balance=principal_decimal,
            currency_code=currency_code,
            interest_rate=Decimal(str(interest_rate)),
            payment_amount=Decimal(str(payment_amount)),
            payment_frequency=payment_frequency,
            start_date=start_date,
            expected_payoff_date=expected_payoff_date,
            next_payment_date=next_payment_date,
            lender=lender,
            account_number_masked=account_number_masked,
            notes=notes,
        )

    @property
    def is_active(self) -> bool:
        """Check if loan is active."""
        return self.status == LoanStatus.ACTIVE

    @property
    def is_paid_off(self) -> bool:
        """Check if loan is paid off."""
        return self.status == LoanStatus.PAID_OFF

    @property
    def money(self) -> Money:
        """Get current balance as Money."""
        return Money.of(self.current_balance, self.currency_code)

    @property
    def principal_paid(self) -> Decimal:
        """Calculate principal paid so far."""
        return self.original_principal - self.current_balance

    @property
    def principal_paid_percentage(self) -> Decimal:
        """Calculate percentage of principal paid."""
        if self.original_principal == Decimal("0"):
            return Decimal("100")
        return (self.principal_paid / self.original_principal) * Decimal("100")

    def record_payment(
        self,
        principal_amount: Decimal | int | float | str,
        interest_amount: Decimal | int | float | str | None = None,
    ) -> None:
        """Record a loan payment.

        Args:
            principal_amount: Amount applied to principal.
            interest_amount: Amount paid as interest (tracked separately).
        """
        if self.status == LoanStatus.PAID_OFF:
            raise ValueError("Cannot record payment on paid-off loan")

        principal = Decimal(str(principal_amount))
        self.current_balance = max(Decimal("0"), self.current_balance - principal)

        if self.current_balance == Decimal("0"):
            self.status = LoanStatus.PAID_OFF

        self.updated_at = _utc_now()

    def update_balance(self, new_balance: Decimal | int | float | str) -> None:
        """Manually update the current balance."""
        self.current_balance = Decimal(str(new_balance))
        if self.current_balance == Decimal("0"):
            self.status = LoanStatus.PAID_OFF
        self.updated_at = _utc_now()


@dataclass
class Transfer:
    """Transfer between two accounts.

    A transfer creates two linked transactions:
    - A debit from the source account
    - A credit to the destination account
    """

    id: UUID
    tenant_id: UUID
    from_account_id: UUID
    to_account_id: UUID
    amount: Decimal
    currency_code: str
    from_transaction_id: UUID | None = None
    to_transaction_id: UUID | None = None
    transfer_date: date = field(default_factory=lambda: date.today())
    description: str = ""
    notes: str | None = None
    exchange_rate: Decimal | None = None
    created_at: datetime = field(default_factory=_utc_now)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: Decimal | int | float | str,
        currency_code: str,
        *,
        transfer_date: date | None = None,
        description: str = "",
        notes: str | None = None,
        exchange_rate: Decimal | int | float | str | None = None,
    ) -> "Transfer":
        """Create a new transfer."""
        if from_account_id == to_account_id:
            raise ValueError("Cannot transfer to the same account")

        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=Decimal(str(amount)),
            currency_code=currency_code,
            transfer_date=transfer_date or date.today(),
            description=description or "Transfer",
            notes=notes,
            exchange_rate=Decimal(str(exchange_rate)) if exchange_rate else None,
        )

    @property
    def money(self) -> Money:
        """Get transfer amount as Money."""
        return Money.of(self.amount, self.currency_code)

    def create_transactions(self) -> tuple[Transaction, Transaction]:
        """Create the debit and credit transactions for this transfer.

        Returns:
            Tuple of (debit_transaction, credit_transaction).
        """
        debit = Transaction.create_debit(
            tenant_id=self.tenant_id,
            account_id=self.from_account_id,
            amount=self.amount,
            currency_code=self.currency_code,
            description=self.description,
            transaction_date=self.transfer_date,
            notes=self.notes,
        )

        credit_amount = self.amount
        if self.exchange_rate:
            credit_amount = self.amount * self.exchange_rate

        credit = Transaction.create_credit(
            tenant_id=self.tenant_id,
            account_id=self.to_account_id,
            amount=credit_amount,
            currency_code=self.currency_code,
            description=self.description,
            transaction_date=self.transfer_date,
            notes=self.notes,
        )

        return debit, credit
