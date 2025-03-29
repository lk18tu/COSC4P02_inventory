from django.urls import path
from .views import history_view

app_name = 'history'

urlpatterns = [
    path('', history_view, name='history'),
]
