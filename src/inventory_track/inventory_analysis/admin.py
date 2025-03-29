from django.contrib import admin
from .models import InventoryItem

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "quantity")
    search_fields = ("name", "category")

admin.site.site_header = "Inventory Management Admin"
