from django.contrib import admin
from .models import InventoryHistory

@admin.register(InventoryHistory)
class InventoryHistoryAdmin(admin.ModelAdmin):
    list_display = ('location', 'action', 'user', 'timestamp', 'details')  
    list_filter = ('action', 'user', 'timestamp')  
    search_fields = ('details', 'item__title', 'user__username')  
    ordering = ('-timestamp',)  
