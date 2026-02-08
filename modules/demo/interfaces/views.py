"""DRF views for the demo module."""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.demo.infrastructure.models import Notification, OutboxEvent


class NotificationListView(APIView):
    """List notifications for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get user's notifications."""
        notifications = Notification.objects.filter(
            user_id=request.user.id,
        ).order_by("-created_at")[:50]

        return Response({
            "data": [
                {
                    "id": str(n.id),
                    "title": n.title,
                    "message": n.message,
                    "type": n.notification_type,
                    "is_read": n.is_read,
                    "action_url": n.action_url,
                    "created_at": n.created_at.isoformat(),
                }
                for n in notifications
            ],
            "meta": {
                "unread_count": Notification.objects.filter(
                    user_id=request.user.id,
                    is_read=False,
                ).count(),
            },
        })


class MarkNotificationReadView(APIView):
    """Mark a notification as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, notification_id: str) -> Response:
        """Mark notification as read."""
        from uuid import UUID

        try:
            notification = Notification.objects.get(
                id=UUID(notification_id),
                user_id=request.user.id,
            )
            notification.mark_as_read()
            return Response({"message": _("Notification marked as read.")})
        except (Notification.DoesNotExist, ValueError):
            return Response(
                {"error": {"code": "NOT_FOUND", "message": _("Notification not found.")}},
                status=status.HTTP_404_NOT_FOUND,
            )


class MarkAllNotificationsReadView(APIView):
    """Mark all notifications as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Mark all notifications as read."""
        from django.utils import timezone

        updated = Notification.objects.filter(
            user_id=request.user.id,
            is_read=False,
        ).update(
            is_read=True,
            read_at=timezone.now(),
        )

        return Response({"message": _("%(count)s notifications marked as read.") % {"count": updated}})


class OutboxStatusView(APIView):
    """Get outbox processing status (admin only)."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get outbox statistics."""
        if not request.user.is_staff:
            return Response(
                {"error": {"code": "FORBIDDEN", "message": _("Admin access required.")}},
                status=status.HTTP_403_FORBIDDEN,
            )

        stats = {
            "pending": OutboxEvent.objects.filter(
                status=OutboxEvent.Status.PENDING
            ).count(),
            "processing": OutboxEvent.objects.filter(
                status=OutboxEvent.Status.PROCESSING
            ).count(),
            "processed": OutboxEvent.objects.filter(
                status=OutboxEvent.Status.PROCESSED
            ).count(),
            "failed": OutboxEvent.objects.filter(
                status=OutboxEvent.Status.FAILED
            ).count(),
        }

        # Get recent failed events
        failed_events = OutboxEvent.objects.filter(
            status=OutboxEvent.Status.FAILED
        ).order_by("-created_at")[:10]

        return Response({
            "stats": stats,
            "recent_failures": [
                {
                    "id": str(e.id),
                    "event_type": e.event_type,
                    "error": e.last_error,
                    "retry_count": e.retry_count,
                    "created_at": e.created_at.isoformat(),
                }
                for e in failed_events
            ],
        })


class TriggerDemoEventView(APIView):
    """Trigger a demo event to test the outbox pattern."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Create a demo event in the outbox."""
        from uuid import uuid4

        from django.db import transaction

        event_data = {
            "event_id": str(uuid4()),
            "event_type": "demo.test_event",
            "occurred_at": request.data.get("message", "Test event"),
        }

        with transaction.atomic():
            outbox_event = OutboxEvent.objects.create(
                event_type="demo.test_event",
                event_id=uuid4(),
                correlation_id=uuid4(),
                tenant_id=request.user.tenant_id,
                payload=event_data,
            )

        return Response({
            "message": _("Demo event created."),
            "event_id": str(outbox_event.event_id),
        }, status=status.HTTP_201_CREATED)
