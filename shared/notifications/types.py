"""Notification types and channels for real-time updates."""

from __future__ import annotations

from enum import Enum


class NotificationType(str, Enum):
    """Types of notifications that can be sent."""

    # System notifications
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

    # Finance notifications
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_POSTED = "transaction.posted"
    TRANSACTION_VOIDED = "transaction.voided"
    BALANCE_UPDATED = "balance.updated"
    TRANSFER_COMPLETED = "transfer.completed"
    ACCOUNT_CREATED = "account.created"
    ACCOUNT_UPDATED = "account.updated"
    ACCOUNT_CLOSED = "account.closed"
    NET_WORTH_UPDATED = "net_worth.updated"
    NET_WORTH_CHANGED = "net_worth.changed"

    # Social finance notifications
    CONTACT_CREATED = "contact.created"
    CONTACT_LINKED = "contact.linked"
    PEER_DEBT_CREATED = "peer_debt.created"
    PEER_DEBT_SETTLED = "peer_debt.settled"
    PEER_DEBT_CANCELLED = "peer_debt.cancelled"
    GROUP_EXPENSE_CREATED = "group_expense.created"
    GROUP_EXPENSE_UPDATED = "group_expense.updated"
    GROUP_MEMBER_ADDED = "group.member_added"
    GROUP_MEMBER_REMOVED = "group.member_removed"
    EXPENSE_SPLIT_SETTLED = "expense_split.settled"
    SETTLEMENT_CREATED = "settlement.created"
    SETTLEMENT_RECORDED = "settlement.recorded"
    BALANCE_WITH_CONTACT_CHANGED = "balance.contact_changed"
    GROUP_BALANCE_CHANGED = "balance.group_changed"


class NotificationChannel(str, Enum):
    """WebSocket channels for notifications."""

    # User-specific notifications
    USER_NOTIFICATIONS = "notifications_{user_id}"

    # Finance-specific channels
    FINANCE_UPDATES = "finance_{user_id}"
    ACCOUNT_UPDATES = "account_{account_id}"

    # Social finance channels
    SOCIAL_UPDATES = "social_{user_id}"
    CONTACT_UPDATES = "contact_{contact_id}"
    EXPENSE_GROUP_UPDATES = "expense_group_{group_id}"

    # System-wide
    SYSTEM_STATUS = "system_status"

    def format(self, **kwargs) -> str:
        """Format the channel name with provided values."""
        return self.value.format(**kwargs)
