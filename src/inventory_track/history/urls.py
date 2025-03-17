from django.urls import path
from .views import history_view

urlpatterns = [
    path('', history_view, name='history'),
]
