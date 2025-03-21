from django.urls import path
from .views import llm_advisor, search_inventory, inventory_chart

app_name = 'inventory_analysis'

urlpatterns = [
    path("advisor/", llm_advisor, name="llm_advisor"),
    path("search/", search_inventory, name="search_inventory"),
    path("chart/", inventory_chart, name="chart"),  # Use name "chart"
]
