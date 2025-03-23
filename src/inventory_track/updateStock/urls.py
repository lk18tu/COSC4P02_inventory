# updateStock/urls.py
from django.urls import path
from .views import product_list, update_stock

app_name = 'updateStock'

urlpatterns = [
    path('products/', product_list, name='product_list'),
    path('update/<str:table_name>/<int:item_id>/', update_stock, name='update_stock'),
]
