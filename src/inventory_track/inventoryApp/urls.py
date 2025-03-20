# inventoryApp/urls.py
from django.urls import path
from . import views

app_name = "inventoryApp"

urlpatterns = [
    path("", views.home, name="home"),
    path("add_inventory/", views.add_inventory, name="add_inventory"),
    path("add_item/<str:table_name>/", views.add_item, name="add_item"),
    path("edit_item/<str:table_name>/<int:item_id>/", views.edit_item, name="edit_item"),
    path("delete_item/<str:table_name>/<int:item_id>/", views.delete_item, name="delete_item"),
    path("add_custom_field/", views.add_custom_field, name="add_custom_field"),
    path("archive_table/<str:table_name>/", views.add_custom_field, name="archive_table"),
    path("upload_csv/<str:table_name>/", views.add_custom_field, name="upload_csv"),
]
