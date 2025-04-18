from django.urls import path
from . import views

app_name = "updateStock"

urlpatterns = [
    # 1) Dashboard / product list
    path("products/", views.product_list, name="product_list"),

    # 2) Detail for one item: list units + remove buttons + history
    path(
        "products/<str:table_name>/<int:item_id>/",
        views.item_detail,
        name="item_detail"
    ),

    # 3) Add stock form
    path(
        "products/<str:table_name>/<int:item_id>/add/",
        views.add_stock,
        name="add_stock"
    ),

    # (Unused bulk‐remove stub, but declared for completeness)
    path(
        "products/<str:table_name>/<int:item_id>/remove/",
        views.remove_stock,
        name="remove_stock"
    ),
]
