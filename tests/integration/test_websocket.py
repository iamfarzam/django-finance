"""Integration tests for WebSocket consumers.

These tests verify the WebSocket consumers work correctly with
the channel layer and authentication.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from channels.testing import WebsocketCommunicator
from rest_framework_simplejwt.tokens import AccessToken

from shared.consumers.base import AuthenticatedConsumer
from shared.consumers.finance import FinanceConsumer
from shared.consumers.health import (
    BackpressureHandler,
    ConnectionState,
    HealthMonitor,
)
from shared.consumers.social import SocialConsumer
from shared.notifications.service import NotificationPayload, NotificationService
from shared.notifications.types import NotificationChannel, NotificationType


class TestConnectionState:
    """Tests for ConnectionState dataclass."""

    def test_record_ping(self):
        """Test recording a ping."""
        state = ConnectionState()
        initial_ping = state.last_ping

        state.record_ping()

        assert state.last_ping >= initial_ping

    def test_record_pong(self):
        """Test recording a pong."""
        state = ConnectionState()
        state.missed_pongs = 3

        state.record_pong()

        assert state.last_pong is not None
        assert state.missed_pongs == 0

    def test_record_message_incoming(self):
        """Test recording an incoming message."""
        state = ConnectionState()

        state.record_message(100, is_incoming=True)

        assert state.message_count == 1
        assert state.bytes_received == 100
        assert state.bytes_sent == 0

    def test_record_message_outgoing(self):
        """Test recording an outgoing message."""
        state = ConnectionState()

        state.record_message(200, is_incoming=False)

        assert state.message_count == 1
        assert state.bytes_sent == 200
        assert state.bytes_received == 0

    def test_get_latency_no_pong(self):
        """Test latency calculation without pong."""
        state = ConnectionState()

        assert state.get_latency_ms() is None

    def test_get_latency_with_pong(self):
        """Test latency calculation with pong."""
        state = ConnectionState()
        state.record_ping()
        state.record_pong()

        latency = state.get_latency_ms()

        assert latency is not None
        assert latency >= 0

    def test_to_dict(self):
        """Test conversion to dictionary."""
        state = ConnectionState(user_id="user-123")

        result = state.to_dict()

        assert "connection_id" in result
        assert result["user_id"] == "user-123"
        assert "connected_at" in result
        assert "is_healthy" in result


class TestHealthMonitor:
    """Tests for HealthMonitor class."""

    def test_register_connection(self):
        """Test registering a connection."""
        monitor = HealthMonitor()

        state = monitor.register_connection("channel-1", user_id="user-1")

        assert state.user_id == "user-1"
        assert monitor.get_connection_state("channel-1") is not None

    def test_unregister_connection(self):
        """Test unregistering a connection."""
        monitor = HealthMonitor()
        monitor.register_connection("channel-1")

        monitor.unregister_connection("channel-1")

        assert monitor.get_connection_state("channel-1") is None

    def test_record_pong(self):
        """Test recording pong."""
        monitor = HealthMonitor()
        state = monitor.register_connection("channel-1")

        monitor.record_pong("channel-1")

        assert state.last_pong is not None

    def test_record_message(self):
        """Test recording message."""
        monitor = HealthMonitor()
        state = monitor.register_connection("channel-1")

        monitor.record_message("channel-1", 100)

        assert state.message_count == 1
        assert state.bytes_received == 100

    def test_get_all_stats(self):
        """Test getting all connection stats."""
        monitor = HealthMonitor()
        monitor.register_connection("channel-1", user_id="user-1")
        monitor.register_connection("channel-2", user_id="user-2")

        stats = monitor.get_all_stats()

        assert len(stats) == 2
        assert "channel-1" in stats
        assert "channel-2" in stats

    def test_get_unhealthy_connections(self):
        """Test getting unhealthy connections."""
        monitor = HealthMonitor()
        state1 = monitor.register_connection("channel-1")
        state2 = monitor.register_connection("channel-2")
        state2.mark_unhealthy()

        unhealthy = monitor.get_unhealthy_connections()

        assert len(unhealthy) == 1
        assert "channel-2" in unhealthy


class TestBackpressureHandler:
    """Tests for BackpressureHandler class."""

    def test_register_connection(self):
        """Test registering a connection."""
        handler = BackpressureHandler()

        handler.register_connection("channel-1")

        assert handler.get_queue_size("channel-1") == 0

    def test_unregister_connection(self):
        """Test unregistering a connection."""
        handler = BackpressureHandler()
        handler.register_connection("channel-1")

        handler.unregister_connection("channel-1")

        assert handler.get_queue_size("channel-1") == 0

    @pytest.mark.asyncio
    async def test_queue_message(self):
        """Test queuing a message."""
        handler = BackpressureHandler()
        handler.register_connection("channel-1")

        result = await handler.queue_message("channel-1", {"type": "test"})

        assert result is True
        assert handler.get_queue_size("channel-1") == 1

    @pytest.mark.asyncio
    async def test_queue_message_unregistered(self):
        """Test queuing to unregistered connection."""
        handler = BackpressureHandler()

        result = await handler.queue_message("channel-1", {"type": "test"})

        assert result is False

    def test_is_backpressure_active(self):
        """Test backpressure status check."""
        handler = BackpressureHandler()
        handler.register_connection("channel-1")

        assert handler.is_backpressure_active("channel-1") is False


class TestNotificationPayload:
    """Tests for NotificationPayload dataclass."""

    def test_create_payload(self):
        """Test creating a notification payload."""
        payload = NotificationPayload(
            notification_type=NotificationType.TRANSACTION_CREATED,
            title="Test Title",
            message="Test Message",
            data={"key": "value"},
        )

        assert payload.notification_type == NotificationType.TRANSACTION_CREATED
        assert payload.title == "Test Title"
        assert payload.notification_id is not None

    def test_to_dict(self):
        """Test payload serialization."""
        payload = NotificationPayload(
            notification_type=NotificationType.INFO,
            title="Test",
            message="Message",
        )

        result = payload.to_dict()

        assert result["notification_type"] == "info"
        assert result["title"] == "Test"
        assert "notification_id" in result
        assert "timestamp" in result


class TestNotificationChannel:
    """Tests for NotificationChannel enum."""

    def test_user_notifications_format(self):
        """Test formatting user notifications channel."""
        user_id = uuid4()

        channel = NotificationChannel.USER_NOTIFICATIONS.format(user_id=user_id)

        assert channel == f"notifications_{user_id}"

    def test_finance_updates_format(self):
        """Test formatting finance updates channel."""
        user_id = uuid4()

        channel = NotificationChannel.FINANCE_UPDATES.format(user_id=user_id)

        assert channel == f"finance_{user_id}"

    def test_account_updates_format(self):
        """Test formatting account updates channel."""
        account_id = uuid4()

        channel = NotificationChannel.ACCOUNT_UPDATES.format(account_id=account_id)

        assert channel == f"account_{account_id}"

    def test_expense_group_updates_format(self):
        """Test formatting expense group updates channel."""
        group_id = uuid4()

        channel = NotificationChannel.EXPENSE_GROUP_UPDATES.format(group_id=group_id)

        assert channel == f"expense_group_{group_id}"


class TestNotificationService:
    """Tests for NotificationService class."""

    def test_service_initialization(self):
        """Test service initializes with lazy channel layer."""
        service = NotificationService()

        assert service._channel_layer is None

    @patch("shared.notifications.service.get_channel_layer")
    def test_send_to_user(self, mock_get_channel_layer):
        """Test sending notification to user."""
        mock_channel_layer = MagicMock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        service = NotificationService()
        user_id = uuid4()

        with patch("shared.notifications.service.async_to_sync") as mock_async_to_sync:
            mock_async_to_sync.return_value = lambda *args: None
            service.send_to_user(
                user_id=user_id,
                notification_type=NotificationType.INFO,
                title="Test",
                message="Test message",
            )

        mock_async_to_sync.assert_called()

    @patch("shared.notifications.service.get_channel_layer")
    def test_send_finance_update(self, mock_get_channel_layer):
        """Test sending finance update."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        service = NotificationService()
        user_id = uuid4()

        with patch("shared.notifications.service.async_to_sync") as mock_async_to_sync:
            mock_async_to_sync.return_value = lambda *args: None
            service.send_finance_update(
                user_id=user_id,
                notification_type=NotificationType.BALANCE_UPDATED,
                title="Balance Updated",
                message="Your balance changed",
                data={"new_balance": "1000.00"},
            )

        # Should be called twice (finance channel + user notification)
        assert mock_async_to_sync.call_count == 2

    @patch("shared.notifications.service.get_channel_layer")
    def test_send_social_update(self, mock_get_channel_layer):
        """Test sending social update."""
        mock_channel_layer = MagicMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        service = NotificationService()
        user_id = uuid4()

        with patch("shared.notifications.service.async_to_sync") as mock_async_to_sync:
            mock_async_to_sync.return_value = lambda *args: None
            service.send_social_update(
                user_id=user_id,
                notification_type=NotificationType.PEER_DEBT_CREATED,
                title="Debt Recorded",
                message="New peer debt",
            )

        # Should be called twice (social channel + user notification)
        assert mock_async_to_sync.call_count == 2


@pytest.fixture
def mock_jwt_token():
    """Create a mock JWT token for testing."""
    user_id = uuid4()
    tenant_id = uuid4()
    token_data = {
        "user_id": str(user_id),
        "tenant_id": str(tenant_id),
    }
    return token_data, user_id, tenant_id


class TestAuthenticatedConsumerBase:
    """Tests for AuthenticatedConsumer base class."""

    @pytest.mark.asyncio
    async def test_ping_pong(self):
        """Test ping/pong heartbeat."""
        consumer = AuthenticatedConsumer()
        consumer.require_auth = False
        consumer.scope = {"query_string": b""}
        consumer.channel_layer = AsyncMock()
        consumer.channel_name = "test-channel"

        communicator = WebsocketCommunicator(
            AuthenticatedConsumer.as_asgi(),
            "/ws/test/",
        )

        # The consumer requires a channel layer to be configured
        # For unit tests, we mock the behavior
        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            consumer.last_ping = datetime.now(timezone.utc)
            await consumer.receive_json({"type": "ping"})

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "pong"


class TestFinanceConsumerHandlers:
    """Tests for FinanceConsumer message handlers."""

    @pytest.mark.asyncio
    async def test_finance_update_handler(self):
        """Test finance update event handler."""
        consumer = FinanceConsumer()
        consumer.scope = {"query_string": b""}

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            event = {
                "notification_type": "balance.updated",
                "title": "Balance Updated",
                "message": "Your balance changed",
                "data": {"account_id": str(uuid4())},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.finance_update(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "finance_update"

    @pytest.mark.asyncio
    async def test_balance_update_handler(self):
        """Test balance update event handler."""
        consumer = FinanceConsumer()

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            event = {
                "account_id": str(uuid4()),
                "new_balance": "1500.00",
                "currency": "USD",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.balance_update(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "balance_update"
            assert call_args["new_balance"] == "1500.00"

    @pytest.mark.asyncio
    async def test_transaction_notification_handler(self):
        """Test transaction notification event handler."""
        consumer = FinanceConsumer()

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            event = {
                "transaction_id": str(uuid4()),
                "action": "created",
                "amount": "100.00",
                "account_id": str(uuid4()),
                "description": "Test transaction",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.transaction_notification(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "transaction"
            assert call_args["action"] == "created"


class TestSocialConsumerHandlers:
    """Tests for SocialConsumer message handlers."""

    @pytest.mark.asyncio
    async def test_social_update_handler(self):
        """Test social update event handler."""
        consumer = SocialConsumer()
        consumer.subscribed_groups = set()

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            event = {
                "notification_type": "peer_debt.created",
                "title": "Debt Recorded",
                "message": "You lent $50 to John",
                "data": {"debt_id": str(uuid4())},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.social_update(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "social_update"

    @pytest.mark.asyncio
    async def test_peer_debt_update_handler(self):
        """Test peer debt update event handler."""
        consumer = SocialConsumer()
        consumer.subscribed_groups = set()

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            event = {
                "debt_id": str(uuid4()),
                "action": "created",
                "contact_id": str(uuid4()),
                "amount": "75.00",
                "direction": "lent",
                "remaining": "75.00",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.peer_debt_update(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "peer_debt_update"
            assert call_args["action"] == "created"

    @pytest.mark.asyncio
    async def test_settlement_update_handler(self):
        """Test settlement update event handler."""
        consumer = SocialConsumer()
        consumer.subscribed_groups = set()

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            event = {
                "settlement_id": str(uuid4()),
                "contact_id": str(uuid4()),
                "amount": "50.00",
                "from_is_owner": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.settlement_update(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "settlement_update"

    @pytest.mark.asyncio
    async def test_balance_changed_handler(self):
        """Test balance changed event handler."""
        consumer = SocialConsumer()
        consumer.subscribed_groups = set()

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            event = {
                "contact_id": str(uuid4()),
                "contact_name": "John Doe",
                "net_balance": "25.00",
                "they_owe_you": "25.00",
                "you_owe_them": "0.00",
                "currency": "USD",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.balance_changed(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "balance_changed"
            assert call_args["contact_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_expense_group_update_handler(self):
        """Test expense group update event handler."""
        consumer = SocialConsumer()
        consumer.subscribed_groups = set()

        with patch.object(consumer, "send_json", new_callable=AsyncMock) as mock_send:
            group_id = str(uuid4())
            event = {
                "notification_type": "group_expense.created",
                "title": "New Expense",
                "message": "Dinner: $120",
                "data": {"group_id": group_id},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await consumer.expense_group_update(event)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            assert call_args["type"] == "expense_group_update"
            assert call_args["group_id"] == group_id
