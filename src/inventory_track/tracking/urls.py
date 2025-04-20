from django.urls import path
from . import views

app_name = 'tracking'

urlpatterns = [
    path('', views.tracking_home, name='tracking_home'),
    path('item/<str:tracking_number>/', views.tracked_item_detail, name='tracked_item_detail'),
    path('qr/', views.generate_qr, name='generate_qr'),
]
