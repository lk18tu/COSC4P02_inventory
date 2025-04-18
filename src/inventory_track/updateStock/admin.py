# updateStock/admin.py
from django.contrib import admin
from .models import StockTransaction

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "table_meta",
        "item_id",
        "change",
        "transaction_id",
        "created_at",
    )
    readonly_fields = (
        "transaction_id",
        "created_at",
    )
    list_filter = (
        "table_meta",
        "change",
    )
    search_fields = (
        "transaction_id",
        "item_id",
    )
