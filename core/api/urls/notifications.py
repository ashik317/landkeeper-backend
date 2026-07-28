from django.urls import path
from api.views.notifications import (
    NotificationListAPIView,
    NotificationUnreadCountAPIView,
    NotificationMarkAllAsReadAPIView,
    NotificationDetailAPIView,
    NotificationMarkAsReadAPIView
)

urlpatterns = [
    path(
        "",
        NotificationListAPIView.as_view(),
        name="notification-list"
    ),
    path(
        "/<int:id>",
        NotificationDetailAPIView.as_view(),
        name="notification-detail"
    ),
    path(
        "/<int:id>/mark-as-read",
        NotificationMarkAsReadAPIView.as_view(),
        name="notification-mark-as-read"
    ),
    path(
        "/unread-count",
        NotificationUnreadCountAPIView.as_view(),
        name="notification-unread-count"
    ),
    path(
        "/mark-all-as-read",
        NotificationMarkAllAsReadAPIView.as_view(),
        name="notification-mark-all-as-read"
    ),
]