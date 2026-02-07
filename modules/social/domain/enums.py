"""Enumerations for the social finance domain."""

from enum import Enum


class DebtDirection(str, Enum):
    """Direction of a peer debt from the perspective of the owner."""

    LENT = "lent"  # Owner lent money to contact (contact owes owner)
    BORROWED = "borrowed"  # Owner borrowed from contact (owner owes contact)

    @property
    def opposite(self) -> "DebtDirection":
        """Get the opposite direction."""
        return DebtDirection.BORROWED if self == DebtDirection.LENT else DebtDirection.LENT

    @property
    def sign(self) -> int:
        """Get the sign for balance calculation.

        From owner's perspective:
        - LENT (positive): Contact owes owner money
        - BORROWED (negative): Owner owes contact money
        """
        return 1 if self == DebtDirection.LENT else -1


class DebtStatus(str, Enum):
    """Status of a peer debt."""

    ACTIVE = "active"  # Debt is active and not fully settled
    SETTLED = "settled"  # Debt has been fully settled
    CANCELLED = "cancelled"  # Debt was cancelled/forgiven


class SplitMethod(str, Enum):
    """Method for splitting a group expense."""

    EQUAL = "equal"  # Split equally among all participants
    EXACT = "exact"  # Exact amounts specified per participant
    PERCENTAGE = "percentage"  # Percentage-based split (future)
    SHARES = "shares"  # Shares/units-based split (future)


class ExpenseStatus(str, Enum):
    """Status of a group expense."""

    ACTIVE = "active"  # Expense is active
    SETTLED = "settled"  # All splits have been settled
    CANCELLED = "cancelled"  # Expense was cancelled


class SplitStatus(str, Enum):
    """Status of an expense split for a participant."""

    PENDING = "pending"  # Not yet settled
    SETTLED = "settled"  # Fully settled
    PARTIAL = "partial"  # Partially settled


class SettlementMethod(str, Enum):
    """Method used for settlement."""

    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    PAYPAL = "paypal"
    VENMO = "venmo"
    OTHER = "other"


class ContactStatus(str, Enum):
    """Status of a contact."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ShareStatus(str, Enum):
    """Status of sharing with a contact who is a registered user."""

    NOT_SHARED = "not_shared"  # Not shared with the contact
    PENDING = "pending"  # Invitation sent, awaiting acceptance
    ACCEPTED = "accepted"  # Contact has accepted and can see shared records
    DECLINED = "declined"  # Contact declined the invitation
