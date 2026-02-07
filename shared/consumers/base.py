"""Base WebSocket consumer with authentication."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger(__name__)


class AuthenticatedConsumer(AsyncJsonWebsocketConsumer):
    """Base consumer with JWT authentication support.

    Subclasses should implement:
        - get_groups(): Return list of channel groups to subscribe to
        - handle_message(): Handle incoming messages from client
    """

    # Connection state
    user_id: str | None = None
    tenant_id: str | None = None
    connected_at: datetime | None = None
    last_ping: datetime | None = None

    # Configuration
    require_auth: bool = True
    ping_interval: int = 30  # seconds
    max_message_size: int = 64 * 1024  # 64KB

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        if self.require_auth:
            if not await self._authenticate():
                await self.close(code=4001)
                return

        self.connected_at = datetime.now(timezone.utc)
        self.last_ping = self.connected_at

        # Subscribe to groups
        for group in await self.get_groups():
            await self.channel_layer.group_add(group, self.channel_name)

        await self.accept()

        # Send connection confirmation
        await self.send_json({
            "type": "connection.established",
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
        })

        logger.info(
            "WebSocket connected",
            extra={
                "user_id": self.user_id,
                "tenant_id": self.tenant_id,
                "consumer": self.__class__.__name__,
            },
        )

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        # Unsubscribe from groups
        for group in await self.get_groups():
            await self.channel_layer.group_discard(group, self.channel_name)

        logger.info(
            "WebSocket disconnected",
            extra={
                "user_id": self.user_id,
                "close_code": close_code,
                "consumer": self.__class__.__name__,
            },
        )

    async def receive_json(self, content: dict[str, Any]) -> None:
        """Handle incoming JSON message."""
        message_type = content.get("type", "")

        # Handle ping/pong for connection health
        if message_type == "ping":
            self.last_ping = datetime.now(timezone.utc)
            await self.send_json({"type": "pong", "timestamp": self.last_ping.isoformat()})
            return

        # Handle subscription management
        if message_type == "subscribe":
            await self._handle_subscribe(content)
            return

        if message_type == "unsubscribe":
            await self._handle_unsubscribe(content)
            return

        # Delegate to subclass handler
        await self.handle_message(content)

    async def get_groups(self) -> list[str]:
        """Get list of channel groups to subscribe to.

        Override in subclasses to customize group subscriptions.

        Returns:
            List of group names.
        """
        return []

    async def handle_message(self, content: dict[str, Any]) -> None:
        """Handle incoming message from client.

        Override in subclasses to handle custom message types.

        Args:
            content: The message content.
        """
        logger.warning(
            "Unhandled message type",
            extra={
                "type": content.get("type"),
                "user_id": self.user_id,
            },
        )

    async def _authenticate(self) -> bool:
        """Authenticate the WebSocket connection using JWT.

        Returns:
            True if authentication successful, False otherwise.
        """
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token_list = params.get("token", [])

        if not token_list:
            logger.warning("WebSocket connection without token")
            return False

        token = token_list[0]

        try:
            access_token = AccessToken(token)
            self.user_id = str(access_token.get("user_id"))
            self.tenant_id = str(access_token.get("tenant_id", self.user_id))
            return True
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Invalid WebSocket token: {e}")
            return False

    async def _handle_subscribe(self, content: dict[str, Any]) -> None:
        """Handle subscription request."""
        channel = content.get("channel")
        if not channel:
            await self.send_json({
                "type": "error",
                "message": "Channel name required for subscription",
            })
            return

        # Validate channel access (subclasses can override)
        if not await self.can_subscribe(channel):
            await self.send_json({
                "type": "error",
                "message": f"Not authorized to subscribe to {channel}",
            })
            return

        await self.channel_layer.group_add(channel, self.channel_name)
        await self.send_json({
            "type": "subscribed",
            "channel": channel,
        })

    async def _handle_unsubscribe(self, content: dict[str, Any]) -> None:
        """Handle unsubscription request."""
        channel = content.get("channel")
        if not channel:
            return

        await self.channel_layer.group_discard(channel, self.channel_name)
        await self.send_json({
            "type": "unsubscribed",
            "channel": channel,
        })

    async def can_subscribe(self, channel: str) -> bool:
        """Check if user can subscribe to a channel.

        Override in subclasses to implement access control.

        Args:
            channel: The channel name.

        Returns:
            True if subscription is allowed.
        """
        # By default, only allow user-specific channels
        if self.user_id and self.user_id in channel:
            return True
        return False

    # Message handlers for channel layer events
    async def notification_message(self, event: dict[str, Any]) -> None:
        """Handle notification message from channel layer."""
        await self.send_json({
            "type": "notification",
            **{k: v for k, v in event.items() if k != "type"},
        })

    async def status_update(self, event: dict[str, Any]) -> None:
        """Handle status update from channel layer."""
        await self.send_json({
            "type": "status",
            **{k: v for k, v in event.items() if k != "type"},
        })
