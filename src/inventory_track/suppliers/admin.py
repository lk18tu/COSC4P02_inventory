from django.contrib import admin
from .models import Supplier, SupplyOrder, SupplyOrderItem


class SupplyOrderItemInline(admin.TabularInline):
    model = SupplyOrderItem
    extra = 1
    
    
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number')
    search_fields = ('name',)

@admin.register(SupplyOrder)
class SupplyOrderAdmin(admin.ModelAdmin):
    list_display = ('tracking_number', 'supplier', 'status', 'location_name', 'created_at')
    list_filter = ('status', 'supplier')
    readonly_fields = ('tracking_number', 'created_at', 'updated_at')

@admin.register(SupplyOrderItem)
class SupplyOrderItemAdmin(admin.ModelAdmin):
    list_display = ('supply_order', 'inventory_item', 'quantity')

