from django.urls import path
from . import views

app_name = 'messaging'  # Define the app name which will be used as namespace
urlpatterns = [
    path("send/", views.send_message, name="send_message"),
    path("inbox/", views.inbox, name="inbox"),
    path("message/<int:message_id>/", views.read_message, name="read_message"),
]
