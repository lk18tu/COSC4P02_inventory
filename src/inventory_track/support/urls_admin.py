from django.urls import path
from . import views_admin  # Use a separate views file for admin

app_name = "support_admin"  # Different namespace

urlpatterns = [
    path("", views_admin.support_admin_login, name="support_admin_login"),
    path("dashboard/", views_admin.support_admin_dashboard, name="support_admin_dashboard"),
    path("logout/", views_admin.support_admin_logout, name="support_admin_logout"),
    path("update-ticket/<int:ticket_id>/", views_admin.update_ticket, name="update_ticket"),
]
