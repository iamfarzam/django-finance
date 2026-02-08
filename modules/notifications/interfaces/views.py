"""DRF views for notifications."""

from __future__ import annotations

from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.notifications.infrastructure.models import (
    Notification,
    NotificationPreference,
)
from modules.notifications.infrastructure.repositories import (
    NotificationRepository,
    PreferenceRepository,
)
from modules.notifications.interfaces.serializers import (
    NotificationSerializer,
    NotificationPreferenceSerializer,
    UpdatePreferenceSerializer,
)


class NotificationListView(APIView):
    """List notifications for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get user's notifications.

        Query parameters:
        - unread_only: bool - Only return unread notifications
        - category: str - Filter by category
        - limit: int - Max notifications to return (default 50)
        """
        repo = NotificationRepository()

        unread_only = request.query_params.get("unread_only", "").lower() == "true"
        category = request.query_params.get("category")
        limit = min(int(request.query_params.get("limit", 50)), 100)

        notifications = repo.get_for_user(
            user_id=request.user.id,
            unread_only=unread_only,
            category=category,
            limit=limit,
        )

        unread_count = repo.get_unread_count(request.user.id)

        return Response({
            "data": NotificationSerializer(notifications, many=True).data,
            "meta": {
                "unread_count": unread_count,
                "total": len(notifications),
            },
        })


class NotificationDetailView(APIView):
    """Get or update a specific notification."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, notification_id: str) -> Response:
        """Get a notification by ID."""
        from uuid import UUID

        repo = NotificationRepository()

        try:
            notification = repo.get_by_id(UUID(notification_id))
            if notification is None or notification.user_id != request.user.id:
                return Response(
                    {"error": {"code": "NOT_FOUND", "message": _("Notification not found.")}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(NotificationSerializer(notification).data)

        except ValueError:
            return Response(
                {"error": {"code": "INVALID_ID", "message": _("Invalid notification ID.")}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MarkNotificationReadView(APIView):
    """Mark a notification as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, notification_id: str) -> Response:
        """Mark notification as read."""
        from uuid import UUID

        repo = NotificationRepository()

        try:
            success = repo.mark_read(UUID(notification_id), request.user.id)
            if not success:
                return Response(
                    {"error": {"code": "NOT_FOUND", "message": _("Notification not found.")}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response({"message": _("Notification marked as read.")})

        except ValueError:
            return Response(
                {"error": {"code": "INVALID_ID", "message": _("Invalid notification ID.")}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MarkAllReadView(APIView):
    """Mark all notifications as read."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """Mark all notifications as read.

        Optional body:
        - category: str - Only mark notifications in this category as read
        """
        repo = NotificationRepository()
        category = request.data.get("category")

        count = repo.mark_all_read(request.user.id, category)

        return Response({
            "message": _("%(count)s notifications marked as read.") % {"count": count},
            "count": count,
        })


class ArchiveNotificationView(APIView):
    """Archive a notification."""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, notification_id: str) -> Response:
        """Archive a notification."""
        from uuid import UUID

        repo = NotificationRepository()

        try:
            success = repo.archive(UUID(notification_id), request.user.id)
            if not success:
                return Response(
                    {"error": {"code": "NOT_FOUND", "message": _("Notification not found.")}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response({"message": _("Notification archived.")})

        except ValueError:
            return Response(
                {"error": {"code": "INVALID_ID", "message": _("Invalid notification ID.")}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UnreadCountView(APIView):
    """Get unread notification count."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get count of unread notifications."""
        repo = NotificationRepository()
        count = repo.get_unread_count(request.user.id)

        return Response({"unread_count": count})


class PreferencesListView(APIView):
    """List notification preferences."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Get user's notification preferences."""
        repo = PreferenceRepository()
        preferences = repo.get_for_user(request.user.id, request.user.tenant_id)

        return Response({
            "data": NotificationPreferenceSerializer(preferences, many=True).data,
        })


class PreferenceUpdateView(APIView):
    """Update notification preferences for a category."""

    permission_classes = [IsAuthenticated]

    def patch(self, request: Request, category: str) -> Response:
        """Update preferences for a category."""
        # Validate category
        valid_categories = [c.value for c in Notification.Category]
        if category not in valid_categories:
            return Response(
                {"error": {"code": "INVALID_CATEGORY", "message": _("Invalid category. Must be one of: %(categories)s") % {"categories": valid_categories}}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UpdatePreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        repo = PreferenceRepository()

        # Get or create preference
        preference = repo.get_for_category(request.user.id, category)
        if preference is None:
            preference = NotificationPreference.objects.create(
                user_id=request.user.id,
                tenant_id=request.user.tenant_id,
                category=category,
            )

        # Update fields
        for field, value in serializer.validated_data.items():
            setattr(preference, field, value)
        preference.save()

        return Response(NotificationPreferenceSerializer(preference).data)
