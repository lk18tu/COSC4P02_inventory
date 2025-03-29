from django.contrib import admin
from .models import Supplier, SupplyOrder, SupplyOrderItem

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number')
    search_fields = ('name', 'email')

@admin.register(SupplyOrder)
class SupplyOrderAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'order_date', 'status')
    list_filter = ('status',)
    search_fields = ('supplier__name',)

@admin.register(SupplyOrderItem)
class SupplyOrderItemAdmin(admin.ModelAdmin):
    list_display = ('supply_order', 'inventory_item', 'quantity')
    search_fields = ('inventory_item__title', 'supply_order__supplier__name')
