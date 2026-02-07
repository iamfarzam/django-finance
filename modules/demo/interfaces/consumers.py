"""WebSocket consumers for the demo module.

Implements JWT-authenticated WebSocket connections for real-time notifications.
"""

from __future__ import annotations

import json
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

import structlog

logger = structlog.get_logger()


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time notifications.

    Authenticates users via JWT token and subscribes them to
    their personal notification channel.

    Usage:
        Connect with JWT token in query string:
        ws://localhost:8000/ws/notifications/?token=<jwt_access_token>
    """

    user_id: str | None = None
    tenant_id: str | None = None
    group_name: str | None = None

    async def connect(self) -> None:
        """Handle WebSocket connection.

        Authenticates user via JWT token and joins notification group.
        """
        # Get token from query string
        query_string = self.scope.get("query_string", b"").decode()
        params = dict(
            param.split("=") for param in query_string.split("&") if "=" in param
        )
        token_str = params.get("token", "")

        if not token_str:
            logger.warning("websocket_auth_failed", reason="missing_token")
            await self.close(code=4001)
            return

        # Validate token
        try:
            token = AccessToken(token_str)
            self.user_id = str(token["user_id"])
            self.tenant_id = str(token.get("tenant_id", ""))

            # Join user's notification group
            self.group_name = f"notifications_{self.user_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)

            await self.accept()

            logger.info(
                "websocket_connected",
                user_id=self.user_id,
                tenant_id=self.tenant_id,
                group_name=self.group_name,
            )

            # Send connection confirmation
            await self.send_json({
                "type": "connection.established",
                "data": {
                    "message": "Connected to notification service",
                    "user_id": self.user_id,
                },
            })

        except (InvalidToken, TokenError) as e:
            logger.warning(
                "websocket_auth_failed",
                reason="invalid_token",
                error=str(e),
            )
            await self.close(code=4001)

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection.

        Args:
            close_code: The close code.
        """
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

            logger.info(
                "websocket_disconnected",
                user_id=self.user_id,
                close_code=close_code,
            )

    async def receive_json(self, content: dict[str, Any]) -> None:
        """Handle incoming WebSocket messages.

        Args:
            content: The received JSON message.
        """
        message_type = content.get("type", "")

        if message_type == "ping":
            await self.send_json({"type": "pong"})

        elif message_type == "mark_read":
            notification_id = content.get("notification_id")
            if notification_id:
                await self._mark_notification_read(notification_id)

        else:
            logger.debug(
                "websocket_message_received",
                user_id=self.user_id,
                message_type=message_type,
            )

    async def notification_message(self, event: dict[str, Any]) -> None:
        """Handle notification message from channel layer.

        Args:
            event: The event data from channel layer.
        """
        await self.send_json({
            "type": "notification",
            "data": event["data"],
        })

    @database_sync_to_async
    def _mark_notification_read(self, notification_id: str) -> None:
        """Mark a notification as read.

        Args:
            notification_id: The notification ID.
        """
        from uuid import UUID

        from modules.demo.infrastructure.models import Notification

        try:
            notification = Notification.objects.get(
                id=UUID(notification_id),
                user_id=UUID(self.user_id),
            )
            notification.mark_as_read()
        except (Notification.DoesNotExist, ValueError):
            pass


class StatusConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for system status updates.

    Broadcasts system-wide status updates to all connected clients.
    Does not require authentication.
    """

    async def connect(self) -> None:
        """Handle WebSocket connection."""
        await self.channel_layer.group_add("system_status", self.channel_name)
        await self.accept()

        await self.send_json({
            "type": "connection.established",
            "data": {"message": "Connected to status service"},
        })

    async def disconnect(self, close_code: int) -> None:
        """Handle WebSocket disconnection."""
        await self.channel_layer.group_discard("system_status", self.channel_name)

    async def status_update(self, event: dict[str, Any]) -> None:
        """Handle status update from channel layer."""
        await self.send_json({
            "type": "status",
            "data": event["data"],
        })
