from django.urls import path
from .views import NotificationListView, NotificationDetailView, clear_read_notifications

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("<int:pk>/", NotificationDetailView.as_view(), name="notification-detail"),
    path("clear/", clear_read_notifications, name="notification-clear"),
]
