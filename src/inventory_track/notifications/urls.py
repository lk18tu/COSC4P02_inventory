from django.urls import path
from . import views

urlpatterns = [
    path("send-notification/", views.send_notification, name="send_notification"),
    path("", views.view_notifications, name="view_notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
]
