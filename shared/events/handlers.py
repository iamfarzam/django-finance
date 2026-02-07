"""Event handlers for real-time notifications.

This module provides handlers that subscribe to domain events and
dispatch real-time notifications to connected WebSocket clients.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from shared.notifications.service import notification_service
from shared.notifications.types import NotificationType

logger = logging.getLogger(__name__)


class FinanceEventHandler:
    """Handler for finance domain events.

    Converts finance domain events into real-time notifications.
    """

    def handle_account_created(
        self,
        user_id: UUID,
        account_id: UUID,
        name: str,
        account_type: str,
        currency_code: str,
    ) -> None:
        """Handle account created event."""
        notification_service.send_finance_update(
            user_id=user_id,
            notification_type=NotificationType.ACCOUNT_CREATED,
            title="Account Created",
            message=f"New {account_type.lower()} account '{name}' has been created.",
            data={
                "account_id": str(account_id),
                "name": name,
                "account_type": account_type,
                "currency_code": currency_code,
            },
        )

    def handle_account_updated(
        self,
        user_id: UUID,
        account_id: UUID,
        name: str,
        updated_fields: list[str],
    ) -> None:
        """Handle account updated event."""
        notification_service.send_account_update(
            account_id=account_id,
            user_id=user_id,
            notification_type=NotificationType.ACCOUNT_UPDATED,
            title="Account Updated",
            message=f"Account '{name}' has been updated.",
            data={
                "updated_fields": updated_fields,
            },
        )

    def handle_account_closed(
        self,
        user_id: UUID,
        account_id: UUID,
        name: str,
        final_balance: str,
    ) -> None:
        """Handle account closed event."""
        notification_service.send_account_update(
            account_id=account_id,
            user_id=user_id,
            notification_type=NotificationType.ACCOUNT_CLOSED,
            title="Account Closed",
            message=f"Account '{name}' has been closed.",
            data={
                "final_balance": final_balance,
            },
        )

    def handle_transaction_created(
        self,
        user_id: UUID,
        account_id: UUID,
        transaction_id: UUID,
        transaction_type: str,
        amount: str,
        currency_code: str,
        description: str | None = None,
    ) -> None:
        """Handle transaction created event."""
        notification_service.send_finance_update(
            user_id=user_id,
            notification_type=NotificationType.TRANSACTION_CREATED,
            title="Transaction Created",
            message=f"New {transaction_type} of {amount} {currency_code}",
            data={
                "transaction_id": str(transaction_id),
                "account_id": str(account_id),
                "transaction_type": transaction_type,
                "amount": amount,
                "currency_code": currency_code,
                "description": description,
            },
        )

    def handle_transaction_posted(
        self,
        user_id: UUID,
        account_id: UUID,
        transaction_id: UUID,
        amount: str,
        new_balance: str,
        currency_code: str,
    ) -> None:
        """Handle transaction posted event."""
        notification_service.send_account_update(
            account_id=account_id,
            user_id=user_id,
            notification_type=NotificationType.BALANCE_UPDATED,
            title="Balance Updated",
            message=f"Account balance is now {new_balance} {currency_code}",
            data={
                "transaction_id": str(transaction_id),
                "amount": amount,
                "new_balance": new_balance,
                "currency_code": currency_code,
            },
        )

    def handle_transfer_completed(
        self,
        user_id: UUID,
        transfer_id: UUID,
        from_account_id: UUID,
        to_account_id: UUID,
        amount: str,
        currency_code: str,
    ) -> None:
        """Handle transfer completed event."""
        notification_service.send_finance_update(
            user_id=user_id,
            notification_type=NotificationType.TRANSFER_COMPLETED,
            title="Transfer Completed",
            message=f"Transfer of {amount} {currency_code} completed.",
            data={
                "transfer_id": str(transfer_id),
                "from_account_id": str(from_account_id),
                "to_account_id": str(to_account_id),
                "amount": amount,
                "currency_code": currency_code,
            },
        )

    def handle_net_worth_updated(
        self,
        user_id: UUID,
        total_assets: str,
        total_liabilities: str,
        net_worth: str,
        currency_code: str,
    ) -> None:
        """Handle net worth updated event."""
        notification_service.send_finance_update(
            user_id=user_id,
            notification_type=NotificationType.NET_WORTH_UPDATED,
            title="Net Worth Updated",
            message=f"Your net worth is {net_worth} {currency_code}",
            data={
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "net_worth": net_worth,
                "currency_code": currency_code,
            },
        )


class SocialEventHandler:
    """Handler for social finance domain events.

    Converts social domain events into real-time notifications.
    """

    def handle_peer_debt_created(
        self,
        user_id: UUID,
        debt_id: UUID,
        contact_id: UUID,
        contact_name: str,
        direction: str,
        amount: str,
        currency_code: str,
    ) -> None:
        """Handle peer debt created event."""
        if direction == "lent":
            message = f"You lent {amount} {currency_code} to {contact_name}"
        else:
            message = f"You borrowed {amount} {currency_code} from {contact_name}"

        notification_service.send_social_update(
            user_id=user_id,
            notification_type=NotificationType.PEER_DEBT_CREATED,
            title="Peer Debt Recorded",
            message=message,
            data={
                "debt_id": str(debt_id),
                "contact_id": str(contact_id),
                "contact_name": contact_name,
                "direction": direction,
                "amount": amount,
                "currency_code": currency_code,
            },
        )

    def handle_peer_debt_settled(
        self,
        user_id: UUID,
        debt_id: UUID,
        contact_id: UUID,
        contact_name: str,
        settlement_amount: str,
        remaining_amount: str,
        is_fully_settled: bool,
        currency_code: str,
    ) -> None:
        """Handle peer debt settled event."""
        if is_fully_settled:
            message = f"Debt with {contact_name} fully settled"
        else:
            message = f"Partial settlement of {settlement_amount} {currency_code} with {contact_name}"

        notification_service.send_social_update(
            user_id=user_id,
            notification_type=NotificationType.PEER_DEBT_SETTLED,
            title="Debt Settled",
            message=message,
            data={
                "debt_id": str(debt_id),
                "contact_id": str(contact_id),
                "contact_name": contact_name,
                "settlement_amount": settlement_amount,
                "remaining_amount": remaining_amount,
                "is_fully_settled": is_fully_settled,
                "currency_code": currency_code,
            },
        )

    def handle_group_expense_created(
        self,
        user_id: UUID,
        group_id: UUID,
        expense_id: UUID,
        group_name: str,
        description: str,
        total_amount: str,
        currency_code: str,
        member_user_ids: list[UUID],
    ) -> None:
        """Handle group expense created event."""
        notification_service.send_expense_group_update(
            group_id=group_id,
            member_user_ids=member_user_ids,
            notification_type=NotificationType.GROUP_EXPENSE_CREATED,
            title="New Group Expense",
            message=f"'{description}' for {total_amount} {currency_code} in {group_name}",
            data={
                "expense_id": str(expense_id),
                "group_id": str(group_id),
                "group_name": group_name,
                "description": description,
                "total_amount": total_amount,
                "currency_code": currency_code,
            },
        )

    def handle_expense_group_member_added(
        self,
        user_id: UUID,
        group_id: UUID,
        group_name: str,
        contact_id: UUID,
        contact_name: str,
        member_user_ids: list[UUID],
    ) -> None:
        """Handle expense group member added event."""
        notification_service.send_expense_group_update(
            group_id=group_id,
            member_user_ids=member_user_ids,
            notification_type=NotificationType.GROUP_MEMBER_ADDED,
            title="New Member",
            message=f"{contact_name} has been added to {group_name}",
            data={
                "group_id": str(group_id),
                "group_name": group_name,
                "contact_id": str(contact_id),
                "contact_name": contact_name,
            },
        )

    def handle_settlement_created(
        self,
        user_id: UUID,
        settlement_id: UUID,
        contact_id: UUID,
        contact_name: str,
        amount: str,
        currency_code: str,
        from_is_owner: bool,
    ) -> None:
        """Handle settlement created event."""
        if from_is_owner:
            message = f"You paid {amount} {currency_code} to {contact_name}"
        else:
            message = f"{contact_name} paid you {amount} {currency_code}"

        notification_service.send_social_update(
            user_id=user_id,
            notification_type=NotificationType.SETTLEMENT_RECORDED,
            title="Settlement Recorded",
            message=message,
            data={
                "settlement_id": str(settlement_id),
                "contact_id": str(contact_id),
                "contact_name": contact_name,
                "amount": amount,
                "currency_code": currency_code,
                "from_is_owner": from_is_owner,
            },
        )

    def handle_balance_updated(
        self,
        user_id: UUID,
        contact_id: UUID,
        contact_name: str,
        net_balance: str,
        currency_code: str,
        balance_direction: str,
    ) -> None:
        """Handle balance updated event."""
        if balance_direction == "they_owe_you":
            message = f"{contact_name} owes you {net_balance} {currency_code}"
        elif balance_direction == "you_owe_them":
            message = f"You owe {contact_name} {net_balance} {currency_code}"
        else:
            message = f"You are settled up with {contact_name}"

        notification_service.send_social_update(
            user_id=user_id,
            notification_type=NotificationType.BALANCE_UPDATED,
            title="Balance Changed",
            message=message,
            data={
                "contact_id": str(contact_id),
                "contact_name": contact_name,
                "net_balance": net_balance,
                "currency_code": currency_code,
                "balance_direction": balance_direction,
            },
        )


# Singleton instances
finance_event_handler = FinanceEventHandler()
social_event_handler = SocialEventHandler()


def register_event_handlers() -> None:
    """Register event handlers with the event bus.

    This function should be called during application startup
    to connect domain events to their handlers.

    Note: The actual event bus integration depends on the
    chosen event infrastructure (Django signals, Celery, etc.)
    """
    # TODO: Integrate with event bus when available
    # For now, handlers are called directly from use cases
    logger.info("Event handlers registered for real-time notifications")
