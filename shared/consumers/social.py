"""Social finance WebSocket consumer for real-time updates."""

from __future__ import annotations

import logging
from typing import Any

from shared.consumers.base import AuthenticatedConsumer
from shared.notifications.types import NotificationChannel

logger = logging.getLogger(__name__)


class SocialConsumer(AuthenticatedConsumer):
    """WebSocket consumer for social finance real-time updates.

    Provides real-time updates for:
    - Peer debt changes
    - Group expense notifications
    - Settlement updates
    - Balance changes with contacts

    Connect via: ws://host/ws/social/?token=<jwt_access_token>
    """

    # Track subscribed expense groups
    subscribed_groups: set[str]

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        self.subscribed_groups = set()
        await super().connect()

    async def get_groups(self) -> list[str]:
        """Get social finance groups to subscribe to."""
        if not self.user_id:
            return []

        return [
            # User's social updates channel
            NotificationChannel.SOCIAL_UPDATES.format(user_id=self.user_id),
            # General notifications
            NotificationChannel.USER_NOTIFICATIONS.format(user_id=self.user_id),
        ]

    async def handle_message(self, content: dict[str, Any]) -> None:
        """Handle incoming messages from client."""
        message_type = content.get("type", "")

        if message_type == "subscribe_group":
            await self._subscribe_to_group(content.get("group_id"))
        elif message_type == "unsubscribe_group":
            await self._unsubscribe_from_group(content.get("group_id"))
        elif message_type == "get_status":
            await self._send_status()
        else:
            await super().handle_message(content)

    async def can_subscribe(self, channel: str) -> bool:
        """Check if user can subscribe to a channel."""
        # Allow user's own channels
        if self.user_id and self.user_id in channel:
            return True

        # Allow expense group channels the user is a member of
        if channel.startswith("expense_group_"):
            # In production, verify group membership
            return True

        return False

    async def _subscribe_to_group(self, group_id: str | None) -> None:
        """Subscribe to an expense group's updates."""
        if not group_id:
            await self.send_json({
                "type": "error",
                "message": "group_id is required",
            })
            return

        channel = NotificationChannel.EXPENSE_GROUP_UPDATES.format(group_id=group_id)
        await self.channel_layer.group_add(channel, self.channel_name)
        self.subscribed_groups.add(group_id)

        await self.send_json({
            "type": "subscribed",
            "channel": "expense_group",
            "group_id": group_id,
        })

        logger.debug(
            "Subscribed to expense group updates",
            extra={
                "user_id": self.user_id,
                "group_id": group_id,
            },
        )

    async def _unsubscribe_from_group(self, group_id: str | None) -> None:
        """Unsubscribe from an expense group's updates."""
        if not group_id:
            return

        channel = NotificationChannel.EXPENSE_GROUP_UPDATES.format(group_id=group_id)
        await self.channel_layer.group_discard(channel, self.channel_name)
        self.subscribed_groups.discard(group_id)

        await self.send_json({
            "type": "unsubscribed",
            "channel": "expense_group",
            "group_id": group_id,
        })

    async def _send_status(self) -> None:
        """Send current connection status."""
        await self.send_json({
            "type": "status",
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "subscribed_groups": list(self.subscribed_groups),
        })

    # Channel layer event handlers

    async def social_update(self, event: dict[str, Any]) -> None:
        """Handle social update from channel layer."""
        await self.send_json({
            "type": "social_update",
            "notification_type": event.get("notification_type"),
            "title": event.get("title"),
            "message": event.get("message"),
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp"),
        })

    async def expense_group_update(self, event: dict[str, Any]) -> None:
        """Handle expense group update from channel layer."""
        await self.send_json({
            "type": "expense_group_update",
            "notification_type": event.get("notification_type"),
            "group_id": event.get("data", {}).get("group_id"),
            "title": event.get("title"),
            "message": event.get("message"),
            "data": event.get("data", {}),
            "timestamp": event.get("timestamp"),
        })

    async def peer_debt_update(self, event: dict[str, Any]) -> None:
        """Handle peer debt update from channel layer."""
        await self.send_json({
            "type": "peer_debt_update",
            "debt_id": event.get("debt_id"),
            "action": event.get("action"),  # created, settled, cancelled
            "contact_id": event.get("contact_id"),
            "amount": event.get("amount"),
            "direction": event.get("direction"),
            "remaining": event.get("remaining"),
            "timestamp": event.get("timestamp"),
        })

    async def settlement_update(self, event: dict[str, Any]) -> None:
        """Handle settlement update from channel layer."""
        await self.send_json({
            "type": "settlement_update",
            "settlement_id": event.get("settlement_id"),
            "contact_id": event.get("contact_id"),
            "amount": event.get("amount"),
            "from_is_owner": event.get("from_is_owner"),
            "timestamp": event.get("timestamp"),
        })

    async def balance_changed(self, event: dict[str, Any]) -> None:
        """Handle balance change with contact from channel layer."""
        await self.send_json({
            "type": "balance_changed",
            "contact_id": event.get("contact_id"),
            "contact_name": event.get("contact_name"),
            "net_balance": event.get("net_balance"),
            "they_owe_you": event.get("they_owe_you"),
            "you_owe_them": event.get("you_owe_them"),
            "currency": event.get("currency"),
            "timestamp": event.get("timestamp"),
        })

    async def group_balance_changed(self, event: dict[str, Any]) -> None:
        """Handle group balance change from channel layer."""
        await self.send_json({
            "type": "group_balance_changed",
            "group_id": event.get("group_id"),
            "entries": event.get("entries", []),
            "total_expenses": event.get("total_expenses"),
            "currency": event.get("currency"),
            "timestamp": event.get("timestamp"),
        })
