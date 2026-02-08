"""URL configuration for notifications API."""

from django.urls import path

from modules.notifications.interfaces import views

app_name = "notifications"

urlpatterns = [
    # Notifications
    path("", views.NotificationListView.as_view(), name="list"),
    path("unread-count/", views.UnreadCountView.as_view(), name="unread_count"),
    path("mark-all-read/", views.MarkAllReadView.as_view(), name="mark_all_read"),
    path("<str:notification_id>/", views.NotificationDetailView.as_view(), name="detail"),
    path("<str:notification_id>/read/", views.MarkNotificationReadView.as_view(), name="mark_read"),
    path("<str:notification_id>/archive/", views.ArchiveNotificationView.as_view(), name="archive"),

    # Preferences
    path("preferences/", views.PreferencesListView.as_view(), name="preferences_list"),
    path("preferences/<str:category>/", views.PreferenceUpdateView.as_view(), name="preferences_update"),
]
