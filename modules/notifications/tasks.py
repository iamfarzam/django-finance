"""Celery tasks for notification delivery."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

import structlog

logger = structlog.get_logger()


@shared_task(name="notifications.create_notification")
def create_notification(
    user_id: str,
    tenant_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: dict[str, Any] | None = None,
    action_url: str | None = None,
    priority: str = "normal",
    send_email: bool = True,
    send_websocket: bool = True,
) -> str:
    """Create and dispatch a notification.

    Args:
        user_id: Target user ID.
        tenant_id: Tenant context.
        notification_type: Type of notification.
        title: Notification title.
        message: Notification message.
        data: Additional data.
        action_url: Optional action URL.
        priority: Notification priority.
        send_email: Whether to send email.
        send_websocket: Whether to send WebSocket notification.

    Returns:
        Created notification ID.
    """
    from modules.notifications.infrastructure.models import (
        Notification,
        NotificationPreference,
    )

    # Get category from type
    category = notification_type.split(".")[0]

    # Check user preferences
    try:
        preference = NotificationPreference.objects.get(
            user_id=UUID(user_id),
            category=category,
        )
        send_email = send_email and preference.email_enabled
        send_websocket = send_websocket and preference.in_app_enabled

        # Check if this specific type is disabled
        if notification_type in preference.disabled_types:
            logger.info(
                "notification_type_disabled",
                user_id=user_id,
                notification_type=notification_type,
            )
            return ""
    except NotificationPreference.DoesNotExist:
        # Use defaults
        pass

    # Create notification in database
    notification = Notification.objects.create(
        user_id=UUID(user_id),
        tenant_id=UUID(tenant_id),
        notification_type=notification_type,
        category=category,
        title=title,
        message=message,
        data=data or {},
        action_url=action_url or "",
        priority=priority,
    )

    logger.info(
        "notification_created",
        notification_id=str(notification.id),
        user_id=user_id,
        notification_type=notification_type,
    )

    # Dispatch to channels
    if send_websocket:
        send_websocket_notification.delay(
            user_id=user_id,
            notification_id=str(notification.id),
            notification_data=notification_to_dict(notification),
        )

    if send_email:
        send_email_notification.delay(
            user_id=user_id,
            notification_id=str(notification.id),
            title=title,
            message=message,
            action_url=action_url,
        )

    return str(notification.id)


@shared_task(name="notifications.send_websocket_notification")
def send_websocket_notification(
    user_id: str,
    notification_id: str,
    notification_data: dict[str, Any],
) -> bool:
    """Send notification via WebSocket.

    Args:
        user_id: Target user ID.
        notification_id: Notification ID.
        notification_data: Notification data to send.

    Returns:
        True if sent successfully.
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    from modules.notifications.infrastructure.models import Notification

    try:
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

        # Mark as sent
        try:
            notification = Notification.objects.get(id=UUID(notification_id))
            notification.mark_websocket_sent()
        except Notification.DoesNotExist:
            pass

        logger.debug(
            "websocket_notification_sent",
            user_id=user_id,
            notification_id=notification_id,
        )

        return True

    except Exception as e:
        logger.error(
            "websocket_notification_failed",
            user_id=user_id,
            notification_id=notification_id,
            error=str(e),
            exc_info=True,
        )
        return False


@shared_task(name="notifications.send_email_notification")
def send_email_notification(
    user_id: str,
    notification_id: str,
    title: str,
    message: str,
    action_url: str | None = None,
) -> bool:
    """Send notification via email.

    Args:
        user_id: Target user ID.
        notification_id: Notification ID.
        title: Email subject.
        message: Email body.
        action_url: Optional action URL.

    Returns:
        True if sent successfully.
    """
    from modules.accounts.infrastructure.models import User
    from modules.notifications.infrastructure.models import Notification

    try:
        user = User.objects.get(id=UUID(user_id))

        # Build email body
        email_body = f"""
{message}
"""
        if action_url:
            full_url = f"{settings.SITE_URL}{action_url}" if action_url.startswith("/") else action_url
            email_body += f"""
View details: {full_url}
"""

        email_body += """
---
You received this notification from Django Finance.
To manage your notification preferences, visit your settings.
"""

        send_mail(
            subject=f"[Django Finance] {title}",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        # Mark as sent
        try:
            notification = Notification.objects.get(id=UUID(notification_id))
            notification.mark_email_sent()
        except Notification.DoesNotExist:
            pass

        logger.info(
            "email_notification_sent",
            user_id=user_id,
            notification_id=notification_id,
            email=user.email,
        )

        return True

    except User.DoesNotExist:
        logger.error(
            "email_notification_failed_user_not_found",
            user_id=user_id,
            notification_id=notification_id,
        )
        return False

    except Exception as e:
        logger.error(
            "email_notification_failed",
            user_id=user_id,
            notification_id=notification_id,
            error=str(e),
            exc_info=True,
        )
        return False


def notification_to_dict(notification) -> dict[str, Any]:
    """Convert notification model to dictionary."""
    return {
        "id": str(notification.id),
        "notification_type": notification.notification_type,
        "category": notification.category,
        "title": notification.title,
        "message": notification.message,
        "data": notification.data,
        "action_url": notification.action_url,
        "priority": notification.priority,
        "created_at": notification.created_at.isoformat(),
    }


# Convenience functions for creating notifications
def notify_transaction_created(
    user_id: str,
    tenant_id: str,
    transaction_id: str,
    transaction_type: str,
    amount: str,
    account_name: str,
) -> None:
    """Notify user of a new transaction."""
    create_notification.delay(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type="finance.transaction_created",
        title="Transaction Recorded",
        message=f"A {transaction_type} of {amount} was recorded in {account_name}.",
        data={
            "transaction_id": transaction_id,
            "transaction_type": transaction_type,
            "amount": amount,
            "account_name": account_name,
        },
        action_url=f"/transactions/{transaction_id}/",
    )


def notify_debt_created(
    user_id: str,
    tenant_id: str,
    debt_id: str,
    contact_name: str,
    direction: str,
    amount: str,
) -> None:
    """Notify user of a new debt."""
    direction_text = "owes" if direction == "lent" else "lent"
    create_notification.delay(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type="social.debt_created",
        title="New Debt Recorded",
        message=f"{contact_name} {direction_text} you {amount}.",
        data={
            "debt_id": debt_id,
            "contact_name": contact_name,
            "direction": direction,
            "amount": amount,
        },
        action_url=f"/debts/{debt_id}/",
    )


def notify_settlement_received(
    user_id: str,
    tenant_id: str,
    settlement_id: str,
    contact_name: str,
    amount: str,
) -> None:
    """Notify user of a received settlement."""
    create_notification.delay(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type="social.settlement_received",
        title="Payment Received",
        message=f"{contact_name} paid you {amount}.",
        data={
            "settlement_id": settlement_id,
            "contact_name": contact_name,
            "amount": amount,
        },
        action_url=f"/settlements/{settlement_id}/",
    )


def notify_expense_added(
    user_id: str,
    tenant_id: str,
    expense_id: str,
    group_id: str,
    group_name: str,
    payer_name: str,
    description: str,
    amount: str,
    share_amount: str,
) -> None:
    """Notify user of a new group expense."""
    create_notification.delay(
        user_id=user_id,
        tenant_id=tenant_id,
        notification_type="social.expense_added",
        title="New Group Expense",
        message=f"{payer_name} added '{description}' ({amount}) to {group_name}. Your share: {share_amount}.",
        data={
            "expense_id": expense_id,
            "group_id": group_id,
            "group_name": group_name,
            "payer_name": payer_name,
            "description": description,
            "amount": amount,
            "share_amount": share_amount,
        },
        action_url=f"/groups/{group_id}/",
    )
