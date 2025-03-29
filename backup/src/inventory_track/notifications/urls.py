from django.urls import path
from . import views

app_name = "notifications"  

urlpatterns = [
    path("", views.view_notifications, name="view_notifications"),
    path("send-notification/", views.send_notification, name="send_notification"),
    path("<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
]
