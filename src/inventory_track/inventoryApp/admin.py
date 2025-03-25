from django.contrib import admin
from .models import InvItem, InvTable_Metadata

@admin.register(InvItem)
class InvItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'quantity_stock', 'table_name')
    list_filter = ('table_name',)
    search_fields = ('title', 'product_number', 'upc')

admin.site.register(InvTable_Metadata)  
