"""Celery tasks for the demo module.

Implements the outbox pattern dispatcher and notification tasks.
"""

from __future__ import annotations

import json
from typing import Any

from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction
from django.utils import timezone

import structlog

logger = structlog.get_logger()


@shared_task(name="demo.process_outbox")
def process_outbox(batch_size: int = 100) -> dict[str, int]:
    """Process pending outbox events.

    This task polls the outbox table for pending events and
    dispatches them to the appropriate handlers.

    Args:
        batch_size: Maximum number of events to process per run.

    Returns:
        Statistics about processed events.
    """
    from modules.demo.infrastructure.models import OutboxEvent

    stats = {"processed": 0, "failed": 0, "skipped": 0}

    # Get pending events that are ready for processing
    events = OutboxEvent.objects.filter(
        status=OutboxEvent.Status.PENDING,
    ).filter(
        # Either no scheduled time or scheduled time has passed
        scheduled_for__isnull=True
    ) | OutboxEvent.objects.filter(
        status=OutboxEvent.Status.PENDING,
        scheduled_for__lte=timezone.now(),
    )

    events = events.order_by("created_at")[:batch_size]

    for event in events:
        try:
            event.mark_processing()
            dispatch_event(event.event_type, event.payload, event.tenant_id)
            event.mark_processed()
            stats["processed"] += 1

            logger.info(
                "outbox_event_processed",
                event_id=str(event.event_id),
                event_type=event.event_type,
                tenant_id=str(event.tenant_id),
            )

        except Exception as e:
            event.mark_failed(str(e))
            stats["failed"] += 1

            logger.error(
                "outbox_event_failed",
                event_id=str(event.event_id),
                event_type=event.event_type,
                error=str(e),
                retry_count=event.retry_count,
                exc_info=True,
            )

    logger.info("outbox_processing_complete", **stats)
    return stats


def dispatch_event(event_type: str, payload: dict[str, Any], tenant_id: Any) -> None:
    """Dispatch an event to appropriate handlers.

    Args:
        event_type: The event type string.
        payload: The event payload.
        tenant_id: The tenant context.
    """
    # Route events to handlers based on type
    handlers = {
        "accounts.user.created": handle_user_created,
        "accounts.user.logged_in": handle_user_logged_in,
        "accounts.user.password_changed": handle_password_changed,
    }

    handler = handlers.get(event_type)
    if handler:
        handler(payload, tenant_id)
    else:
        logger.debug("no_handler_for_event", event_type=event_type)


def handle_user_created(payload: dict[str, Any], tenant_id: Any) -> None:
    """Handle user created event.

    Args:
        payload: Event payload.
        tenant_id: Tenant context.
    """
    # Send welcome notification
    send_notification.delay(
        user_id=str(payload["user_id"]),
        tenant_id=str(tenant_id),
        title="Welcome!",
        message="Your account has been created successfully.",
        notification_type="success",
    )


def handle_user_logged_in(payload: dict[str, Any], tenant_id: Any) -> None:
    """Handle user login event.

    Args:
        payload: Event payload.
        tenant_id: Tenant context.
    """
    logger.info(
        "user_logged_in_event",
        user_id=payload.get("user_id"),
        tenant_id=str(tenant_id),
    )


def handle_password_changed(payload: dict[str, Any], tenant_id: Any) -> None:
    """Handle password changed event.

    Args:
        payload: Event payload.
        tenant_id: Tenant context.
    """
    # Send security notification
    send_notification.delay(
        user_id=str(payload["user_id"]),
        tenant_id=str(tenant_id),
        title="Password Changed",
        message="Your password has been changed. If you didn't do this, please contact support.",
        notification_type="warning",
    )


@shared_task(name="demo.send_notification")
def send_notification(
    user_id: str,
    tenant_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    action_url: str = "",
) -> str:
    """Send a notification to a user.

    Creates a notification record and sends via WebSocket.

    Args:
        user_id: Target user ID.
        tenant_id: Tenant context.
        title: Notification title.
        message: Notification message.
        notification_type: Type of notification.
        action_url: Optional action URL.

    Returns:
        Created notification ID.
    """
    from uuid import UUID

    from modules.demo.infrastructure.models import Notification

    # Create notification record
    notification = Notification.objects.create(
        user_id=UUID(user_id),
        tenant_id=UUID(tenant_id),
        title=title,
        message=message,
        notification_type=notification_type,
        action_url=action_url,
    )

    # Send via WebSocket
    send_websocket_notification.delay(
        user_id=user_id,
        notification_data={
            "id": str(notification.id),
            "title": notification.title,
            "message": notification.message,
            "type": notification.notification_type,
            "action_url": notification.action_url,
            "created_at": notification.created_at.isoformat(),
        },
    )

    logger.info(
        "notification_created",
        notification_id=str(notification.id),
        user_id=user_id,
        title=title,
    )

    return str(notification.id)


@shared_task(name="demo.send_websocket_notification")
def send_websocket_notification(
    user_id: str,
    notification_data: dict[str, Any],
) -> bool:
    """Send notification via WebSocket.

    Args:
        user_id: Target user ID.
        notification_data: Notification payload.

    Returns:
        True if sent successfully.
    """
    from asgiref.sync import async_to_sync

    channel_layer = get_channel_layer()

    # Send to user's notification channel
    group_name = f"notifications_{user_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notification.message",
            "data": notification_data,
        },
    )

    logger.debug(
        "websocket_notification_sent",
        user_id=user_id,
        group_name=group_name,
    )

    return True


@shared_task(name="demo.cleanup_processed_outbox")
def cleanup_processed_outbox(days_old: int = 7) -> int:
    """Clean up old processed outbox events.

    Args:
        days_old: Delete events older than this many days.

    Returns:
        Number of deleted events.
    """
    from datetime import timedelta

    from modules.demo.infrastructure.models import OutboxEvent

    cutoff = timezone.now() - timedelta(days=days_old)

    deleted, _ = OutboxEvent.objects.filter(
        status=OutboxEvent.Status.PROCESSED,
        processed_at__lt=cutoff,
    ).delete()

    logger.info("outbox_cleanup_complete", deleted_count=deleted, days_old=days_old)

    return deleted
