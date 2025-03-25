from django.utils.deprecation import MiddlewareMixin
from .connection import set_current_tenant
from .models import Tenant
from django.http import Http404

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract tenant from URL path
        path = request.path_info.lstrip('/')
        
        # Default tenant
        company_path = None
        tenant = None
        
        if path:
            parts = path.split('/', 1)
            if len(parts) > 0:
                potential_path = parts[0]
                
                # Skip global URLs
                if potential_path not in ['admin', 'static', 'media', '']: 
                    try:
                        # Try to get the tenant by company_path
                        tenant = Tenant.objects.get(company_path=potential_path)
                        company_path = tenant.company_path
                        # Set the current tenant to its database name
                        set_current_tenant(tenant.db_name)
                        
                        # Update the PATH_INFO to remove the company_path part
                        if len(parts) > 1:
                            request.path_info = '/' + parts[1]
                    except Tenant.DoesNotExist:
                        # If no tenant exists with this path, use default
                        set_current_tenant('default')
        
        # For global URLs, use default
        if not company_path:
            set_current_tenant('default')
        
        # Add tenant info to the request for views to use
        request.company_path = company_path
        request.tenant = tenant
        
        response = self.get_response(request)
        return response 