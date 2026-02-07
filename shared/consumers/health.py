"""Connection health monitoring for WebSocket consumers.

This module provides utilities for monitoring WebSocket connection health,
including ping/pong heartbeats, connection timeouts, and backpressure handling.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable, Coroutine
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger(__name__)


@dataclass
class ConnectionState:
    """State tracking for a WebSocket connection."""

    connection_id: UUID = field(default_factory=uuid4)
    user_id: str | None = None
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_ping: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_pong: datetime | None = None
    message_count: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    is_healthy: bool = True
    missed_pongs: int = 0

    def record_ping(self) -> None:
        """Record that a ping was sent."""
        self.last_ping = datetime.now(timezone.utc)

    def record_pong(self) -> None:
        """Record that a pong was received."""
        self.last_pong = datetime.now(timezone.utc)
        self.missed_pongs = 0

    def record_message(self, size: int, is_incoming: bool = True) -> None:
        """Record a message."""
        self.message_count += 1
        if is_incoming:
            self.bytes_received += size
        else:
            self.bytes_sent += size

    def mark_unhealthy(self) -> None:
        """Mark connection as unhealthy."""
        self.is_healthy = False

    def get_latency_ms(self) -> float | None:
        """Get latency in milliseconds based on last ping/pong."""
        if self.last_pong and self.last_ping:
            delta = self.last_pong - self.last_ping
            return delta.total_seconds() * 1000
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "connection_id": str(self.connection_id),
            "user_id": self.user_id,
            "connected_at": self.connected_at.isoformat(),
            "last_ping": self.last_ping.isoformat(),
            "last_pong": self.last_pong.isoformat() if self.last_pong else None,
            "message_count": self.message_count,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "is_healthy": self.is_healthy,
            "latency_ms": self.get_latency_ms(),
        }


class HealthMonitor:
    """Monitors health of WebSocket connections.

    Provides ping/pong heartbeat functionality, connection timeout detection,
    and health statistics.
    """

    def __init__(
        self,
        ping_interval: int = 30,
        pong_timeout: int = 10,
        max_missed_pongs: int = 3,
    ):
        """Initialize health monitor.

        Args:
            ping_interval: Seconds between ping messages.
            pong_timeout: Seconds to wait for pong response.
            max_missed_pongs: Number of missed pongs before marking unhealthy.
        """
        self.ping_interval = ping_interval
        self.pong_timeout = pong_timeout
        self.max_missed_pongs = max_missed_pongs
        self._connections: dict[str, ConnectionState] = {}
        self._ping_tasks: dict[str, asyncio.Task] = {}

    def register_connection(
        self,
        channel_name: str,
        user_id: str | None = None,
    ) -> ConnectionState:
        """Register a new connection for monitoring.

        Args:
            channel_name: The channel name identifying this connection.
            user_id: Optional user ID associated with the connection.

        Returns:
            The connection state object.
        """
        state = ConnectionState(user_id=user_id)
        self._connections[channel_name] = state
        logger.debug(
            "Registered connection for health monitoring",
            extra={
                "channel_name": channel_name,
                "connection_id": str(state.connection_id),
            },
        )
        return state

    def unregister_connection(self, channel_name: str) -> None:
        """Unregister a connection from monitoring.

        Args:
            channel_name: The channel name identifying this connection.
        """
        # Cancel any running ping task
        if channel_name in self._ping_tasks:
            self._ping_tasks[channel_name].cancel()
            del self._ping_tasks[channel_name]

        if channel_name in self._connections:
            del self._connections[channel_name]
            logger.debug(
                "Unregistered connection from health monitoring",
                extra={"channel_name": channel_name},
            )

    def get_connection_state(self, channel_name: str) -> ConnectionState | None:
        """Get the state of a connection.

        Args:
            channel_name: The channel name identifying this connection.

        Returns:
            The connection state or None if not found.
        """
        return self._connections.get(channel_name)

    def record_pong(self, channel_name: str) -> None:
        """Record a pong received for a connection.

        Args:
            channel_name: The channel name identifying this connection.
        """
        if state := self._connections.get(channel_name):
            state.record_pong()

    def record_message(
        self,
        channel_name: str,
        size: int,
        is_incoming: bool = True,
    ) -> None:
        """Record a message for a connection.

        Args:
            channel_name: The channel name identifying this connection.
            size: Size of the message in bytes.
            is_incoming: Whether this is an incoming message.
        """
        if state := self._connections.get(channel_name):
            state.record_message(size, is_incoming)

    async def start_heartbeat(
        self,
        channel_name: str,
        send_ping: Callable[[], Coroutine[Any, Any, None]],
        on_timeout: Callable[[], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        """Start heartbeat monitoring for a connection.

        Args:
            channel_name: The channel name identifying this connection.
            send_ping: Async function to send a ping message.
            on_timeout: Optional async function to call on timeout.
        """
        if channel_name in self._ping_tasks:
            return

        async def heartbeat_loop() -> None:
            state = self._connections.get(channel_name)
            if not state:
                return

            while True:
                try:
                    await asyncio.sleep(self.ping_interval)

                    # Send ping
                    state.record_ping()
                    await send_ping()

                    # Wait for pong
                    await asyncio.sleep(self.pong_timeout)

                    # Check if pong was received
                    if state.last_pong is None or state.last_pong < state.last_ping:
                        state.missed_pongs += 1
                        logger.warning(
                            "Missed pong from connection",
                            extra={
                                "channel_name": channel_name,
                                "missed_count": state.missed_pongs,
                            },
                        )

                        if state.missed_pongs >= self.max_missed_pongs:
                            state.mark_unhealthy()
                            if on_timeout:
                                await on_timeout()
                            return

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        "Error in heartbeat loop",
                        extra={"channel_name": channel_name, "error": str(e)},
                        exc_info=True,
                    )

        self._ping_tasks[channel_name] = asyncio.create_task(heartbeat_loop())

    def stop_heartbeat(self, channel_name: str) -> None:
        """Stop heartbeat monitoring for a connection.

        Args:
            channel_name: The channel name identifying this connection.
        """
        if channel_name in self._ping_tasks:
            self._ping_tasks[channel_name].cancel()
            del self._ping_tasks[channel_name]

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get health statistics for all connections.

        Returns:
            Dictionary mapping channel names to their stats.
        """
        return {
            channel: state.to_dict()
            for channel, state in self._connections.items()
        }

    def get_unhealthy_connections(self) -> list[str]:
        """Get list of unhealthy connection channel names.

        Returns:
            List of channel names for unhealthy connections.
        """
        return [
            channel
            for channel, state in self._connections.items()
            if not state.is_healthy
        ]


class BackpressureHandler:
    """Handles backpressure for WebSocket message sending.

    Implements rate limiting and queue management to prevent
    overwhelming slow clients.
    """

    def __init__(
        self,
        max_queue_size: int = 100,
        high_watermark: int = 80,
        low_watermark: int = 20,
    ):
        """Initialize backpressure handler.

        Args:
            max_queue_size: Maximum messages to queue before dropping.
            high_watermark: Queue size to start applying backpressure.
            low_watermark: Queue size to stop applying backpressure.
        """
        self.max_queue_size = max_queue_size
        self.high_watermark = high_watermark
        self.low_watermark = low_watermark
        self._queues: dict[str, asyncio.Queue] = {}
        self._backpressure_active: dict[str, bool] = {}
        self._worker_tasks: dict[str, asyncio.Task] = {}

    def register_connection(self, channel_name: str) -> None:
        """Register a connection for backpressure handling.

        Args:
            channel_name: The channel name identifying this connection.
        """
        self._queues[channel_name] = asyncio.Queue(maxsize=self.max_queue_size)
        self._backpressure_active[channel_name] = False

    def unregister_connection(self, channel_name: str) -> None:
        """Unregister a connection from backpressure handling.

        Args:
            channel_name: The channel name identifying this connection.
        """
        if channel_name in self._worker_tasks:
            self._worker_tasks[channel_name].cancel()
            del self._worker_tasks[channel_name]

        self._queues.pop(channel_name, None)
        self._backpressure_active.pop(channel_name, None)

    async def queue_message(
        self,
        channel_name: str,
        message: dict[str, Any],
        priority: int = 0,
    ) -> bool:
        """Queue a message for sending.

        Args:
            channel_name: The channel name identifying this connection.
            message: The message to queue.
            priority: Message priority (higher = more important).

        Returns:
            True if message was queued, False if dropped.
        """
        queue = self._queues.get(channel_name)
        if not queue:
            return False

        # Check if we should drop low-priority messages
        if queue.qsize() >= self.high_watermark:
            self._backpressure_active[channel_name] = True
            if priority <= 0:
                logger.warning(
                    "Dropping low-priority message due to backpressure",
                    extra={"channel_name": channel_name, "queue_size": queue.qsize()},
                )
                return False

        try:
            queue.put_nowait((priority, message))
            return True
        except asyncio.QueueFull:
            logger.warning(
                "Message queue full, dropping message",
                extra={"channel_name": channel_name},
            )
            return False

    async def start_worker(
        self,
        channel_name: str,
        send_func: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        """Start a worker to process queued messages.

        Args:
            channel_name: The channel name identifying this connection.
            send_func: Async function to send a message.
        """
        if channel_name in self._worker_tasks:
            return

        async def worker() -> None:
            queue = self._queues.get(channel_name)
            if not queue:
                return

            while True:
                try:
                    _, message = await queue.get()
                    await send_func(message)

                    # Check if we can release backpressure
                    if queue.qsize() <= self.low_watermark:
                        self._backpressure_active[channel_name] = False

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        "Error in backpressure worker",
                        extra={"channel_name": channel_name, "error": str(e)},
                        exc_info=True,
                    )

        self._worker_tasks[channel_name] = asyncio.create_task(worker())

    def is_backpressure_active(self, channel_name: str) -> bool:
        """Check if backpressure is active for a connection.

        Args:
            channel_name: The channel name identifying this connection.

        Returns:
            True if backpressure is active.
        """
        return self._backpressure_active.get(channel_name, False)

    def get_queue_size(self, channel_name: str) -> int:
        """Get the current queue size for a connection.

        Args:
            channel_name: The channel name identifying this connection.

        Returns:
            Current queue size or 0 if not found.
        """
        queue = self._queues.get(channel_name)
        return queue.qsize() if queue else 0


# Singleton instances
health_monitor = HealthMonitor()
backpressure_handler = BackpressureHandler()
