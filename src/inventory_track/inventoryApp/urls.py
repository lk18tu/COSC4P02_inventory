from django.urls import path
from . import views
from .views import add_item, delete_item, edit_item, add_custom_field, add_inventory

app_name = 'inventoryApp'

urlpatterns = [
    path('', views.home, name="home"),
    path('add-item/<str:table_name>/', views.add_item, name="add_item"),  # Capture table_name
    path("add-inventory/", add_inventory, name="add_inventory"),
    path("delete-item/<int:item_id>/", delete_item, name="delete_item"),
    path("edit/<int:item_id>/", edit_item, name="edit_item"),
    path('add_custom_field/', add_custom_field, name='add_custom_field'),

]