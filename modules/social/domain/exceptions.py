"""Domain exceptions for the social finance module."""

from __future__ import annotations


class SocialFinanceError(Exception):
    """Base exception for social finance domain errors."""

    pass


class ContactError(SocialFinanceError):
    """Error related to contact operations."""

    pass


class ContactNotFoundError(ContactError):
    """Contact not found."""

    def __init__(self, contact_id: str) -> None:
        super().__init__(f"Contact not found: {contact_id}")
        self.contact_id = contact_id


class ContactAlreadyLinkedError(ContactError):
    """Contact is already linked to a user."""

    def __init__(self, contact_id: str) -> None:
        super().__init__(f"Contact already linked to a user: {contact_id}")
        self.contact_id = contact_id


class DebtError(SocialFinanceError):
    """Error related to peer debt operations."""

    pass


class DebtNotFoundError(DebtError):
    """Peer debt not found."""

    def __init__(self, debt_id: str) -> None:
        super().__init__(f"Peer debt not found: {debt_id}")
        self.debt_id = debt_id


class DebtAlreadySettledError(DebtError):
    """Debt has already been settled."""

    def __init__(self, debt_id: str) -> None:
        super().__init__(f"Debt already settled: {debt_id}")
        self.debt_id = debt_id


class InvalidSettlementAmountError(DebtError):
    """Settlement amount is invalid."""

    def __init__(self, amount: str, remaining: str) -> None:
        super().__init__(
            f"Settlement amount {amount} exceeds remaining debt {remaining}"
        )
        self.amount = amount
        self.remaining = remaining


class ExpenseError(SocialFinanceError):
    """Error related to group expense operations."""

    pass


class ExpenseGroupNotFoundError(ExpenseError):
    """Expense group not found."""

    def __init__(self, group_id: str) -> None:
        super().__init__(f"Expense group not found: {group_id}")
        self.group_id = group_id


class ExpenseNotFoundError(ExpenseError):
    """Group expense not found."""

    def __init__(self, expense_id: str) -> None:
        super().__init__(f"Expense not found: {expense_id}")
        self.expense_id = expense_id


class InvalidSplitError(ExpenseError):
    """Split configuration is invalid."""

    pass


class SplitSumMismatchError(InvalidSplitError):
    """Split amounts don't add up to total."""

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"Split total {actual} doesn't match expense total {expected}")
        self.expected = expected
        self.actual = actual


class SettlementError(SocialFinanceError):
    """Error related to settlement operations."""

    pass


class SettlementNotFoundError(SettlementError):
    """Settlement not found."""

    def __init__(self, settlement_id: str) -> None:
        super().__init__(f"Settlement not found: {settlement_id}")
        self.settlement_id = settlement_id


class CurrencyMismatchError(SocialFinanceError):
    """Currencies don't match for the operation."""

    def __init__(self, expected: str, actual: str) -> None:
        super().__init__(f"Currency mismatch: expected {expected}, got {actual}")
        self.expected = expected
        self.actual = actual
