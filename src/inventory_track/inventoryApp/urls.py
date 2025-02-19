from django.urls import path
from . import views
from .views import add_item, delete_item

urlpatterns = [
    path('', views.home, name="home"),
    path("add-item/", views.add_item, name="add_item"),
    path("delete-item/<int:item_id>/", delete_item, name="delete_item")
]