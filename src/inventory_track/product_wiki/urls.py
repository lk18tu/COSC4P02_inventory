from django.urls import path
from .views import generate_product_wiki, view_product_wiki

app_name = "product_wiki"

urlpatterns = [
    path('generate/', generate_product_wiki, name='generate_product_wiki'), # Wiki genaration page
    path("view/", view_product_wiki, name="view_product_wiki"),  # HTML wiki page
]
