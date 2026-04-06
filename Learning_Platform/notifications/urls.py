from django.urls import path

from .views import (
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
    NotificationListView,
)

urlpatterns = [
    path("", NotificationListView.as_view(), name="notifications"),
    path("read-all/", MarkAllNotificationsReadView.as_view(), name="mark-all-notifications-read"),
    path("read/<int:pk>/", MarkNotificationReadView.as_view(), name="mark-notification-read"),
]
