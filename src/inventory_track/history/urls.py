from django.urls import path
from .views import history_view
appname = 'history'
urlpatterns = [
    path('', history_view, name='history'),
]
