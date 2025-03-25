from django.contrib import admin
from .models import Tenant

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_path', 'db_name', 'created_at', 'is_active')
    search_fields = ('name', 'company_path')
    list_filter = ('is_active', 'created_at')
    date_hierarchy = 'created_at'
    readonly_fields = ['db_name', 'created_at']

    def get_queryset(self, request):
        # Only show tenants owned by the current user (unless superuser)
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)
