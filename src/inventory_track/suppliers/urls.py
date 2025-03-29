from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    # Supplier CRUD
    path('supplier_list/', views.supplier_list, name='supplier_list'),
    path('supplier_create/', views.supplier_create, name='supplier_create'),
    path('supplier_edit/<int:pk>/', views.supplier_edit, name='supplier_edit'),
    
    # Supply Order CRUD
    path('order_list/', views.order_list, name='order_list'),
    path('order_create/', views.order_create, name='order_create'),
    path('order_detail/<int:pk>/', views.order_detail, name='order_detail'),
]
