from django.urls import path
from . import views

app_name = 'support'  # Namespace for company-specific support


urlpatterns = [
    # Company-specific support
    path("", views.supportHome, name="supportHome"),
    path("submit-ticket/", views.submit_ticket, name="submit_ticket"),
]


