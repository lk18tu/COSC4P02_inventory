from django.conf import settings
from django.shortcuts import redirect
from django.db import connections
from .models import Tenant
import re

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the hostname from the request
        host = request.get_host().split(':')[0]
        
        # Check if this is a tenant-specific URL
        path_info = request.path_info.lstrip('/')
        if '/' in path_info:
            tenant_url = path_info.split('/')[0]
            
            try:
                # Try to get the tenant by domain_url
                tenant = Tenant.objects.get(domain_url=tenant_url, is_active=True)
                
                # Set the tenant in the request object
                request.tenant = tenant
                
                # Use the tenant's database connection
                # In Django 5.1, we need to use a different approach
                # Instead of ensure_defaults, we'll set the connection directly
                if tenant.schema_name not in connections.databases:
                    # Copy all settings from default database
                    default_settings = connections.databases['default'].copy()
                    
                    # Update with tenant-specific settings
                    connections.databases[tenant.schema_name] = default_settings.copy()
                    connections.databases[tenant.schema_name].update({
                        'NAME': tenant.schema_name,
                        'ATOMIC_REQUESTS': False,
                    })
                
                # Set the tenant's database as the default for this request
                request._db = tenant.schema_name
                
            except Tenant.DoesNotExist:
                # If tenant doesn't exist, continue with default database
                pass
        
        response = self.get_response(request)
        return response
