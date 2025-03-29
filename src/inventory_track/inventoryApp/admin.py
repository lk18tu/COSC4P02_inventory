from django.contrib import admin
from .models import InvItem, InvTable_Metadata

@admin.register(InvItem)
class InvItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'quantity', 'completed')  
