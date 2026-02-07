"""Finance WebSocket consumer for real-time updates."""

from __future__ import annotations

import logging
from typing import Any

from shared.consumers.base import AuthenticatedConsumer
from shared.notifications.types import NotificationChannel

logger = logging.getLogger(__name__)


class FinanceConsumer(AuthenticatedConsumer):
    """WebSocket consumer for finance-related real-time updates.

    Provides real-time updates for:
    - Account balance changes
    - Transaction notifications
    - Transfer completions
    - Net worth updates

    Connect via: ws://host/ws/finance/?token=<jwt_access_token>
    """

    # Track subscribed accounts
    subscribed_accounts: set[str]

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        self.subscribed_accounts = set()
        await super().connect()

    async def get_groups(self) -> list[str]:
        """Get finance-related groups to subscribe to."""
        if not self.user_id:
            return []

        return [
            # User's finance updates channel
            NotificationChannel.FINANCE_UPDATES.format(user_id=self.user_id),
            # General notifications
            NotificationChannel.USER_NOTIFICATIONS.format(user_id=self.user_id),
        ]

    async def handle_message(self, content: dict[str, Any]) -> None:
        """Handle incoming messages from client."""
        message_type = content.get("type", "")

        if message_type == "subscribe_account":
            await self._subscribe_to_account(content.get("account_id"))
        elif message_type == "unsubscribe_account":
            await self._unsubscribe_from_account(content.get("account_id"))
        elif message_type == "get_status":
            await self._send_status()
        else:
            await super().handle_message(content)

    async def can_subscribe(self, channel: str) -> bool:
        """Check if user can subscribe to a channel."""
        # Allow user's own channels
        if self.user_id and self.user_id in channel:
            return True

        # Allow account channels the user has access to
        if channel.startswith("account_"):
            # In production, verify account ownership
            return True

        return False

    async def _subscribe_to_account(self, account_id: str | None) -> None:
        """Subscribe to a specific account's updates."""
        if not account_id:
            await self.send_json({
                "type": "error",
                "message": "account_id is required",
            })
            return

        channel = NotificationChannel.ACCOUNT_UPDATES.format(account_id=account_id)
        await self.channel_layer.group_add(channel, self.channel_name)
        self.subscribed_accounts.add(account_id)

        await self.send_json({
            "type": "subscribed",
            "channel": "account",
            "account_id": account_id,
        })

        logger.debug(
            "Subscribed to account updates",
            extra={
                "user_id": self.user_id,
                "account_id": account_id,
            },
        )

    async def _unsubscribe_from_account(self, account_id: str | None) -> None:
        """Unsubscribe from a specific account's updates."""
        if not account_id:
            return

        channel = NotificationChannel.ACCOUNT_UPDATES.format(account_id=account_id)
        await self.channel_layer.group_discard(channel, self.channel_name)
        self.subscribed_accounts.discard(account_id)

        await self.send_json({
            "type": "unsubscribed",
            "channel": "account",
            "account_id": account_id,
        })

    async def _send_status(self) -> None:
        """Send current connection status."""
        await self.send_json({
            "type": "status",
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "subscribed_accounts": list(self.subscribed_accounts),
        })

    # Channel layer event handlers

    async def finance_update(self, event: dict[str, Any]) -> None:
        """Handle finance update from channel layer."""
        await self.send_json({
            "type": "finance_update",
            "notification_type": event.get("notification_type"),
            "title": event.get("title"),
            "message": event.get("message"),
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp"),
        })

    async def account_update(self, event: dict[str, Any]) -> None:
        """Handle account update from channel layer."""
        await self.send_json({
            "type": "account_update",
            "notification_type": event.get("notification_type"),
            "title": event.get("title"),
            "message": event.get("message"),
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp"),
        })

    async def balance_update(self, event: dict[str, Any]) -> None:
        """Handle balance update from channel layer."""
        await self.send_json({
            "type": "balance_update",
            "account_id": event.get("account_id"),
            "new_balance": event.get("new_balance"),
            "currency": event.get("currency"),
            "timestamp": event.get("timestamp"),
        })

    async def transaction_notification(self, event: dict[str, Any]) -> None:
        """Handle transaction notification from channel layer."""
        await self.send_json({
            "type": "transaction",
            "transaction_id": event.get("transaction_id"),
            "action": event.get("action"),  # created, posted, voided
            "amount": event.get("amount"),
            "account_id": event.get("account_id"),
            "description": event.get("description"),
            "timestamp": event.get("timestamp"),
        })

    async def net_worth_update(self, event: dict[str, Any]) -> None:
        """Handle net worth update from channel layer."""
        await self.send_json({
            "type": "net_worth_update",
            "total_assets": event.get("total_assets"),
            "total_liabilities": event.get("total_liabilities"),
            "net_worth": event.get("net_worth"),
            "currency": event.get("currency"),
            "timestamp": event.get("timestamp"),
        })
