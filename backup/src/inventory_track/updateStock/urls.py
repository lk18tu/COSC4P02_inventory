from django.urls import path
from . import views

app_name = 'updateStock'

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/update/<int:pk>/', views.update_stock, name='update_stock'),
]
