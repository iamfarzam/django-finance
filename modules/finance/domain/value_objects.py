"""Value objects for the finance module.

Value objects are immutable and compared by their attributes, not identity.
They encapsulate domain concepts with validation and behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import ClassVar
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Currency:
    """Currency value object with ISO 4217 code and precision.

    Attributes:
        code: ISO 4217 currency code (e.g., "USD", "EUR").
        decimal_places: Number of decimal places for this currency.
        symbol: Currency symbol for display.
        name: Full currency name.
    """

    code: str
    decimal_places: int
    symbol: str
    name: str

    # Supported currencies with their configurations
    SUPPORTED: ClassVar[dict[str, "Currency"]] = {}

    def __post_init__(self) -> None:
        """Validate currency code format."""
        if len(self.code) != 3 or not self.code.isalpha():
            raise ValueError(f"Invalid currency code: {self.code}")
        if self.decimal_places < 0:
            raise ValueError(f"Invalid decimal places: {self.decimal_places}")

    @classmethod
    def get(cls, code: str) -> "Currency":
        """Get a supported currency by code.

        Args:
            code: ISO 4217 currency code.

        Returns:
            Currency instance.

        Raises:
            ValueError: If currency is not supported.
        """
        code = code.upper()
        if code not in cls.SUPPORTED:
            raise ValueError(f"Unsupported currency: {code}")
        return cls.SUPPORTED[code]

    @classmethod
    def is_supported(cls, code: str) -> bool:
        """Check if a currency code is supported."""
        return code.upper() in cls.SUPPORTED

    def __str__(self) -> str:
        return self.code


# Initialize supported currencies
Currency.SUPPORTED = {
    "USD": Currency("USD", 2, "$", "US Dollar"),
    "EUR": Currency("EUR", 2, "\u20ac", "Euro"),
    "GBP": Currency("GBP", 2, "\u00a3", "British Pound"),
    "CAD": Currency("CAD", 2, "C$", "Canadian Dollar"),
    "AUD": Currency("AUD", 2, "A$", "Australian Dollar"),
    "JPY": Currency("JPY", 0, "\u00a5", "Japanese Yen"),
    "INR": Currency("INR", 2, "\u20b9", "Indian Rupee"),
}


@dataclass(frozen=True)
class Money:
    """Money value object with amount and currency.

    Uses Decimal for precise financial calculations.
    Amount is always stored with full precision internally,
    but rounded appropriately for display and persistence.

    Attributes:
        amount: The monetary amount (always positive for transactions).
        currency: The currency of this money.
    """

    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        """Validate and normalize the money value."""
        if not isinstance(self.amount, Decimal):
            # Convert to Decimal if needed
            try:
                object.__setattr__(self, "amount", Decimal(str(self.amount)))
            except (InvalidOperation, ValueError) as e:
                raise ValueError(f"Invalid amount: {self.amount}") from e

    @classmethod
    def of(cls, amount: Decimal | int | float | str, currency_code: str) -> "Money":
        """Create a Money instance from amount and currency code.

        Args:
            amount: The monetary amount.
            currency_code: ISO 4217 currency code.

        Returns:
            Money instance.
        """
        currency = Currency.get(currency_code)
        return cls(amount=Decimal(str(amount)), currency=currency)

    @classmethod
    def zero(cls, currency_code: str) -> "Money":
        """Create a zero Money instance for a currency.

        Args:
            currency_code: ISO 4217 currency code.

        Returns:
            Money instance with zero amount.
        """
        return cls.of(0, currency_code)

    @property
    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == Decimal("0")

    @property
    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > Decimal("0")

    @property
    def is_negative(self) -> bool:
        """Check if amount is negative."""
        return self.amount < Decimal("0")

    def rounded(self) -> "Money":
        """Return a new Money with amount rounded to currency precision.

        Uses ROUND_HALF_UP (banker's rounding) as per financial standards.
        """
        quantize_str = "0." + "0" * self.currency.decimal_places
        if self.currency.decimal_places == 0:
            quantize_str = "1"
        rounded_amount = self.amount.quantize(
            Decimal(quantize_str), rounding=ROUND_HALF_UP
        )
        return Money(amount=rounded_amount, currency=self.currency)

    def __add__(self, other: "Money") -> "Money":
        """Add two Money values."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two Money values."""
        if not isinstance(other, Money):
            return NotImplemented
        self._ensure_same_currency(other)
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: Decimal | int | float) -> "Money":
        """Multiply Money by a factor."""
        return Money(
            amount=self.amount * Decimal(str(factor)), currency=self.currency
        )

    def __neg__(self) -> "Money":
        """Negate the money amount."""
        return Money(amount=-self.amount, currency=self.currency)

    def __abs__(self) -> "Money":
        """Return absolute value."""
        return Money(amount=abs(self.amount), currency=self.currency)

    def __lt__(self, other: "Money") -> bool:
        """Less than comparison."""
        self._ensure_same_currency(other)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison."""
        self._ensure_same_currency(other)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison."""
        self._ensure_same_currency(other)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison."""
        self._ensure_same_currency(other)
        return self.amount >= other.amount

    def _ensure_same_currency(self, other: "Money") -> None:
        """Ensure both Money objects have the same currency."""
        if self.currency.code != other.currency.code:
            raise ValueError(
                f"Cannot operate on different currencies: "
                f"{self.currency.code} vs {other.currency.code}"
            )

    def format(self, show_symbol: bool = True) -> str:
        """Format money for display.

        Args:
            show_symbol: Whether to include currency symbol.

        Returns:
            Formatted string representation.
        """
        rounded = self.rounded()
        if self.currency.decimal_places == 0:
            formatted = f"{rounded.amount:,.0f}"
        else:
            formatted = f"{rounded.amount:,.{self.currency.decimal_places}f}"

        if show_symbol:
            return f"{self.currency.symbol}{formatted}"
        return formatted

    def __str__(self) -> str:
        return self.format()


@dataclass(frozen=True)
class IdempotencyKey:
    """Idempotency key for ensuring exactly-once processing of financial writes.

    Attributes:
        value: The unique key value.
        tenant_id: The tenant this key belongs to.
    """

    value: str
    tenant_id: UUID

    def __post_init__(self) -> None:
        """Validate the idempotency key."""
        if not self.value or len(self.value) > 255:
            raise ValueError("Idempotency key must be 1-255 characters")

    @classmethod
    def generate(cls, tenant_id: UUID) -> "IdempotencyKey":
        """Generate a new idempotency key.

        Args:
            tenant_id: The tenant ID.

        Returns:
            New IdempotencyKey instance.
        """
        return cls(value=str(uuid4()), tenant_id=tenant_id)


@dataclass(frozen=True)
class ExchangeRate:
    """Exchange rate between two currencies at a point in time.

    Attributes:
        from_currency: Source currency code.
        to_currency: Target currency code.
        rate: The exchange rate (1 from_currency = rate to_currency).
        timestamp: When this rate was recorded.
    """

    from_currency: str
    to_currency: str
    rate: Decimal

    def __post_init__(self) -> None:
        """Validate exchange rate."""
        if self.rate <= Decimal("0"):
            raise ValueError("Exchange rate must be positive")

    def convert(self, money: Money) -> Money:
        """Convert money using this exchange rate.

        Args:
            money: The money to convert.

        Returns:
            Converted money in target currency.
        """
        if money.currency.code != self.from_currency:
            raise ValueError(
                f"Money currency {money.currency.code} doesn't match "
                f"exchange rate from currency {self.from_currency}"
            )
        converted_amount = money.amount * self.rate
        return Money.of(converted_amount, self.to_currency)

    def inverse(self) -> "ExchangeRate":
        """Get the inverse exchange rate."""
        return ExchangeRate(
            from_currency=self.to_currency,
            to_currency=self.from_currency,
            rate=Decimal("1") / self.rate,
        )
