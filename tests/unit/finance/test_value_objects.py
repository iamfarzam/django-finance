"""Unit tests for finance domain value objects."""

from decimal import Decimal
from uuid import uuid4

import pytest

from modules.finance.domain.value_objects import (
    Currency,
    ExchangeRate,
    IdempotencyKey,
    Money,
)


class TestCurrency:
    """Tests for Currency value object."""

    def test_get_supported_currency(self):
        """Test getting a supported currency."""
        usd = Currency.get("USD")
        assert usd.code == "USD"
        assert usd.decimal_places == 2
        assert usd.symbol == "$"
        assert usd.name == "US Dollar"

    def test_get_unsupported_currency(self):
        """Test getting an unsupported currency raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported currency"):
            Currency.get("XYZ")

    def test_currency_case_insensitive(self):
        """Test currency lookup is case-insensitive."""
        usd = Currency.get("usd")
        assert usd.code == "USD"

    def test_is_supported(self):
        """Test is_supported check."""
        assert Currency.is_supported("USD")
        assert Currency.is_supported("eur")
        assert not Currency.is_supported("XYZ")

    def test_invalid_currency_code(self):
        """Test that invalid currency codes are rejected."""
        with pytest.raises(ValueError, match="Invalid currency code"):
            Currency("US", 2, "$", "US Dollar")

        with pytest.raises(ValueError, match="Invalid currency code"):
            Currency("USDD", 2, "$", "US Dollar")

    def test_jpy_has_zero_decimal_places(self):
        """Test that JPY has 0 decimal places."""
        jpy = Currency.get("JPY")
        assert jpy.decimal_places == 0


class TestMoney:
    """Tests for Money value object."""

    def test_create_money(self):
        """Test creating Money from amount and currency."""
        money = Money.of(100, "USD")
        assert money.amount == Decimal("100")
        assert money.currency.code == "USD"

    def test_create_money_from_string(self):
        """Test creating Money from string amount."""
        money = Money.of("99.99", "USD")
        assert money.amount == Decimal("99.99")

    def test_create_zero_money(self):
        """Test creating zero Money."""
        money = Money.zero("USD")
        assert money.amount == Decimal("0")
        assert money.is_zero

    def test_is_positive(self):
        """Test is_positive check."""
        assert Money.of(100, "USD").is_positive
        assert not Money.of(0, "USD").is_positive
        assert not Money.of(-100, "USD").is_positive

    def test_is_negative(self):
        """Test is_negative check."""
        assert not Money.of(100, "USD").is_negative
        assert not Money.of(0, "USD").is_negative
        assert Money.of(-100, "USD").is_negative

    def test_add_money(self):
        """Test adding two Money values."""
        a = Money.of(100, "USD")
        b = Money.of(50, "USD")
        result = a + b
        assert result.amount == Decimal("150")
        assert result.currency.code == "USD"

    def test_subtract_money(self):
        """Test subtracting two Money values."""
        a = Money.of(100, "USD")
        b = Money.of(30, "USD")
        result = a - b
        assert result.amount == Decimal("70")

    def test_add_different_currencies_raises(self):
        """Test that adding different currencies raises ValueError."""
        a = Money.of(100, "USD")
        b = Money.of(100, "EUR")
        with pytest.raises(ValueError, match="Cannot operate on different currencies"):
            _ = a + b

    def test_multiply_money(self):
        """Test multiplying Money by a factor."""
        money = Money.of(100, "USD")
        result = money * 2
        assert result.amount == Decimal("200")

    def test_negate_money(self):
        """Test negating Money."""
        money = Money.of(100, "USD")
        result = -money
        assert result.amount == Decimal("-100")

    def test_abs_money(self):
        """Test absolute value of Money."""
        money = Money.of(-100, "USD")
        result = abs(money)
        assert result.amount == Decimal("100")

    def test_rounded_usd(self):
        """Test rounding USD to 2 decimal places."""
        money = Money.of("99.999", "USD")
        rounded = money.rounded()
        assert rounded.amount == Decimal("100.00")

    def test_rounded_jpy(self):
        """Test rounding JPY to 0 decimal places."""
        money = Money.of("999.5", "JPY")
        rounded = money.rounded()
        assert rounded.amount == Decimal("1000")

    def test_format_usd(self):
        """Test formatting USD."""
        money = Money.of("1234.56", "USD")
        assert money.format() == "$1,234.56"
        assert money.format(show_symbol=False) == "1,234.56"

    def test_format_jpy(self):
        """Test formatting JPY (no decimals)."""
        money = Money.of(1000, "JPY")
        assert "\u00a5" in money.format()  # Yen symbol

    def test_comparison(self):
        """Test Money comparisons."""
        a = Money.of(100, "USD")
        b = Money.of(50, "USD")
        c = Money.of(100, "USD")

        assert a > b
        assert b < a
        assert a >= c
        assert a <= c
        assert not a < c
        assert not a > c


class TestIdempotencyKey:
    """Tests for IdempotencyKey value object."""

    def test_create_idempotency_key(self):
        """Test creating an idempotency key."""
        tenant_id = uuid4()
        key = IdempotencyKey(value="test-key-123", tenant_id=tenant_id)
        assert key.value == "test-key-123"
        assert key.tenant_id == tenant_id

    def test_generate_idempotency_key(self):
        """Test generating a random idempotency key."""
        tenant_id = uuid4()
        key = IdempotencyKey.generate(tenant_id)
        assert len(key.value) == 36  # UUID format
        assert key.tenant_id == tenant_id

    def test_empty_key_raises(self):
        """Test that empty key raises ValueError."""
        with pytest.raises(ValueError, match="must be 1-255 characters"):
            IdempotencyKey(value="", tenant_id=uuid4())

    def test_long_key_raises(self):
        """Test that too long key raises ValueError."""
        with pytest.raises(ValueError, match="must be 1-255 characters"):
            IdempotencyKey(value="x" * 256, tenant_id=uuid4())


class TestExchangeRate:
    """Tests for ExchangeRate value object."""

    def test_create_exchange_rate(self):
        """Test creating an exchange rate."""
        rate = ExchangeRate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.85"),
        )
        assert rate.from_currency == "USD"
        assert rate.to_currency == "EUR"
        assert rate.rate == Decimal("0.85")

    def test_convert_money(self):
        """Test converting money using exchange rate."""
        rate = ExchangeRate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.85"),
        )
        usd = Money.of(100, "USD")
        eur = rate.convert(usd)
        assert eur.currency.code == "EUR"
        assert eur.amount == Decimal("85.00")

    def test_convert_wrong_currency_raises(self):
        """Test converting wrong currency raises ValueError."""
        rate = ExchangeRate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.85"),
        )
        gbp = Money.of(100, "GBP")
        with pytest.raises(ValueError, match="doesn't match"):
            rate.convert(gbp)

    def test_inverse_rate(self):
        """Test getting inverse exchange rate."""
        rate = ExchangeRate(
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("0.85"),
        )
        inverse = rate.inverse()
        assert inverse.from_currency == "EUR"
        assert inverse.to_currency == "USD"
        # 1/0.85 = ~1.176
        assert inverse.rate > Decimal("1.17")
        assert inverse.rate < Decimal("1.18")

    def test_zero_rate_raises(self):
        """Test that zero rate raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            ExchangeRate(
                from_currency="USD",
                to_currency="EUR",
                rate=Decimal("0"),
            )
