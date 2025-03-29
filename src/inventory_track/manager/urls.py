from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    path('stock/', views.view_stock, name='view_stock'),
]
