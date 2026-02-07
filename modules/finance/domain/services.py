"""Domain services for the finance module.

Services contain business logic that doesn't naturally fit within a single entity.
They orchestrate operations across multiple entities and enforce business rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from modules.finance.domain.enums import TransactionStatus, TransactionType
from modules.finance.domain.value_objects import Money

if TYPE_CHECKING:
    from collections.abc import Iterable

    from modules.finance.domain.entities import (
        Account,
        Asset,
        Liability,
        Loan,
        Transaction,
    )


@dataclass
class BalanceResult:
    """Result of a balance calculation.

    Attributes:
        balance: The calculated balance.
        total_credits: Sum of all credit transactions.
        total_debits: Sum of all debit transactions.
        transaction_count: Number of transactions included.
        as_of_date: Date the balance is calculated for.
    """

    balance: Money
    total_credits: Money
    total_debits: Money
    transaction_count: int
    as_of_date: date | None = None


class BalanceCalculator:
    """Service for calculating account balances.

    In single-entry accounting, balance is calculated as:
    Balance = SUM(credits) - SUM(debits)

    Only posted transactions are included in balance calculations.
    Pending and voided transactions are excluded.
    """

    @staticmethod
    def calculate(
        transactions: Iterable[Transaction],
        currency_code: str,
        *,
        as_of_date: date | None = None,
        include_pending: bool = False,
    ) -> BalanceResult:
        """Calculate balance from a list of transactions.

        Args:
            transactions: Transactions to calculate balance from.
            currency_code: Currency for the result.
            as_of_date: Optional date to calculate balance as of.
            include_pending: Whether to include pending transactions.

        Returns:
            BalanceResult with balance and breakdown.
        """
        total_credits = Decimal("0")
        total_debits = Decimal("0")
        count = 0

        for tx in transactions:
            # Skip voided transactions
            if tx.status == TransactionStatus.VOIDED:
                continue

            # Skip pending unless explicitly included
            if tx.status == TransactionStatus.PENDING and not include_pending:
                continue

            # Skip transactions after the as_of_date
            if as_of_date and tx.transaction_date > as_of_date:
                continue

            if tx.transaction_type == TransactionType.CREDIT:
                total_credits += tx.amount
            else:
                total_debits += tx.amount

            count += 1

        balance = total_credits - total_debits

        return BalanceResult(
            balance=Money.of(balance, currency_code),
            total_credits=Money.of(total_credits, currency_code),
            total_debits=Money.of(total_debits, currency_code),
            transaction_count=count,
            as_of_date=as_of_date,
        )

    @staticmethod
    def calculate_running_balance(
        transactions: list[Transaction],
        currency_code: str,
        starting_balance: Decimal = Decimal("0"),
    ) -> list[tuple[Transaction, Money]]:
        """Calculate running balance for each transaction.

        Args:
            transactions: Transactions sorted by date.
            currency_code: Currency for balances.
            starting_balance: Initial balance before first transaction.

        Returns:
            List of (transaction, running_balance) tuples.
        """
        result: list[tuple[Transaction, Money]] = []
        current = starting_balance

        for tx in transactions:
            if tx.status == TransactionStatus.VOIDED:
                continue

            current += tx.signed_amount
            result.append((tx, Money.of(current, currency_code)))

        return result


@dataclass
class NetWorthResult:
    """Result of net worth calculation.

    Attributes:
        total_assets: Sum of all asset values.
        total_liabilities: Sum of all liability balances.
        net_worth: Assets minus liabilities.
        account_balances: Sum of account balances.
        asset_count: Number of assets included.
        liability_count: Number of liabilities included.
        account_count: Number of accounts included.
    """

    total_assets: Money
    total_liabilities: Money
    net_worth: Money
    account_balances: Money
    asset_count: int
    liability_count: int
    account_count: int


class NetWorthCalculator:
    """Service for calculating net worth.

    Net Worth = (Account Balances + Asset Values) - Liability Balances

    Only items marked as 'is_included_in_net_worth' are counted.
    """

    @staticmethod
    def calculate(
        accounts: Iterable[tuple[Account, Money]],
        assets: Iterable[Asset],
        liabilities: Iterable[Liability],
        loans: Iterable[Loan],
        base_currency: str,
    ) -> NetWorthResult:
        """Calculate net worth from accounts, assets, and liabilities.

        Args:
            accounts: Iterable of (account, balance) tuples.
            assets: Iterable of assets.
            liabilities: Iterable of liabilities.
            loans: Iterable of loans.
            base_currency: Currency for the result.

        Returns:
            NetWorthResult with breakdown.

        Note:
            Currency conversion should be handled before calling this method.
            All values should be in the base currency.
        """
        total_account_balance = Decimal("0")
        account_count = 0

        for account, balance in accounts:
            if account.is_included_in_net_worth and account.is_active:
                # Assume balance is already converted to base currency
                total_account_balance += balance.amount
                account_count += 1

        total_asset_value = Decimal("0")
        asset_count = 0

        for asset in assets:
            if asset.is_included_in_net_worth:
                total_asset_value += asset.current_value
                asset_count += 1

        total_liability_balance = Decimal("0")
        liability_count = 0

        for liability in liabilities:
            if liability.is_included_in_net_worth:
                total_liability_balance += liability.current_balance
                liability_count += 1

        for loan in loans:
            if loan.is_included_in_net_worth and loan.is_active:
                total_liability_balance += loan.current_balance
                liability_count += 1

        total_assets = total_account_balance + total_asset_value
        net_worth = total_assets - total_liability_balance

        return NetWorthResult(
            total_assets=Money.of(total_asset_value, base_currency),
            total_liabilities=Money.of(total_liability_balance, base_currency),
            net_worth=Money.of(net_worth, base_currency),
            account_balances=Money.of(total_account_balance, base_currency),
            asset_count=asset_count,
            liability_count=liability_count,
            account_count=account_count,
        )


class TransactionValidator:
    """Service for validating transaction operations."""

    @staticmethod
    def validate_amount(amount: Decimal) -> list[str]:
        """Validate a transaction amount.

        Args:
            amount: The amount to validate.

        Returns:
            List of validation error messages.
        """
        errors: list[str] = []

        if amount < Decimal("0"):
            errors.append("Amount cannot be negative")

        if amount == Decimal("0"):
            errors.append("Amount cannot be zero")

        # Check for reasonable precision (up to 8 decimal places)
        if amount.as_tuple().exponent < -8:
            errors.append("Amount has too many decimal places (max 8)")

        return errors

    @staticmethod
    def validate_date(transaction_date: date) -> list[str]:
        """Validate a transaction date.

        Args:
            transaction_date: The date to validate.

        Returns:
            List of validation error messages.
        """
        errors: list[str] = []

        # Don't allow transactions more than 10 years in the past
        min_date = date.today().replace(year=date.today().year - 10)
        if transaction_date < min_date:
            errors.append("Transaction date is too far in the past")

        # Don't allow transactions more than 1 year in the future
        max_date = date.today().replace(year=date.today().year + 1)
        if transaction_date > max_date:
            errors.append("Transaction date is too far in the future")

        return errors


class AccountLimitChecker:
    """Service for checking account limits based on user tier."""

    # Account limits by role
    LIMITS = {
        "user": 3,
        "premium": float("inf"),
        "superadmin": float("inf"),
    }

    @classmethod
    def check_limit(cls, role: str, current_count: int) -> tuple[bool, int]:
        """Check if user can create another account.

        Args:
            role: User's role (user, premium, superadmin).
            current_count: Current number of accounts.

        Returns:
            Tuple of (can_create, limit).
        """
        limit = cls.LIMITS.get(role, 3)
        can_create = current_count < limit
        return can_create, int(limit) if limit != float("inf") else -1


@dataclass
class CashFlowResult:
    """Result of cash flow analysis.

    Attributes:
        total_income: Total credits (money in).
        total_expenses: Total debits (money out).
        net_cash_flow: Income minus expenses.
        income_by_category: Breakdown of income by category.
        expenses_by_category: Breakdown of expenses by category.
    """

    total_income: Money
    total_expenses: Money
    net_cash_flow: Money
    income_by_category: dict[str, Money]
    expenses_by_category: dict[str, Money]


class CashFlowAnalyzer:
    """Service for analyzing cash flow."""

    @staticmethod
    def analyze(
        transactions: Iterable[Transaction],
        category_names: dict[str, str],
        currency_code: str,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> CashFlowResult:
        """Analyze cash flow from transactions.

        Args:
            transactions: Transactions to analyze.
            category_names: Mapping of category_id to name.
            currency_code: Currency for results.
            start_date: Optional start of analysis period.
            end_date: Optional end of analysis period.

        Returns:
            CashFlowResult with analysis.
        """
        income_total = Decimal("0")
        expense_total = Decimal("0")
        income_by_cat: dict[str, Decimal] = {}
        expense_by_cat: dict[str, Decimal] = {}

        for tx in transactions:
            # Skip voided and pending
            if tx.status != TransactionStatus.POSTED:
                continue

            # Filter by date range
            if start_date and tx.transaction_date < start_date:
                continue
            if end_date and tx.transaction_date > end_date:
                continue

            cat_name = (
                category_names.get(str(tx.category_id), "Uncategorized")
                if tx.category_id
                else "Uncategorized"
            )

            if tx.transaction_type == TransactionType.CREDIT:
                income_total += tx.amount
                income_by_cat[cat_name] = income_by_cat.get(cat_name, Decimal("0")) + tx.amount
            else:
                expense_total += tx.amount
                expense_by_cat[cat_name] = expense_by_cat.get(cat_name, Decimal("0")) + tx.amount

        return CashFlowResult(
            total_income=Money.of(income_total, currency_code),
            total_expenses=Money.of(expense_total, currency_code),
            net_cash_flow=Money.of(income_total - expense_total, currency_code),
            income_by_category={k: Money.of(v, currency_code) for k, v in income_by_cat.items()},
            expenses_by_category={k: Money.of(v, currency_code) for k, v in expense_by_cat.items()},
        )
