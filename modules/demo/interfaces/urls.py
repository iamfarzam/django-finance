"""URL configuration for demo module."""

from django.urls import path

from modules.demo.interfaces.views import (
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
    NotificationListView,
    OutboxStatusView,
    TriggerDemoEventView,
)

app_name = "demo"

urlpatterns = [
    # Notifications
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/<str:notification_id>/read/",
        MarkNotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "notifications/read-all/",
        MarkAllNotificationsReadView.as_view(),
        name="notification-read-all",
    ),
    # Outbox (admin)
    path("outbox/status/", OutboxStatusView.as_view(), name="outbox-status"),
    # Demo
    path("trigger-event/", TriggerDemoEventView.as_view(), name="trigger-event"),
]
