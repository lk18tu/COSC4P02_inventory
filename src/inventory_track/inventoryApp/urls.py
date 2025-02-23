from django.urls import path
from . import views
from .views import add_item, delete_item, edit_item

urlpatterns = [
    path('', views.home, name="home"),
    path("add/", add_item, name="add_item"),
    path("delete-item/<int:item_id>/", delete_item, name="delete_item"),
    path("edit/<int:item_id>/", edit_item, name="edit_item")
]