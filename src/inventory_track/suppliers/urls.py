from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.supplier_list,   name='supplier_list'),
    path('create/', views.supplier_create, name='supplier_create'),
    path('<int:pk>/edit/', views.supplier_edit,   name='supplier_edit'),

    path('orders/', views.order_list,   name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/receive/', views.order_receive, name='order_receive'
    ),
]
