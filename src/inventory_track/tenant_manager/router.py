from .connection import get_current_tenant

class TenantRouter:
    """
    Database router that routes queries to the appropriate tenant database
    """
    
    def db_for_read(self, model, **hints):
        tenant = get_current_tenant()
        return tenant

    def db_for_write(self, model, **hints):
        tenant = get_current_tenant()
        return tenant
    
    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations within the same database
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # For the default database
        if db == 'default':
            # Always allow auth app migrations first
            if app_label in ['auth', 'contenttypes', 'sessions', 'admin']:
                return True
            # Always allow tenant_manager app
            if app_label == 'tenant_manager':
                return True
            # For other apps, check if we're syncing new tenants
            return hints.get('tenant') == 'default'
        
        # For tenant databases, only migrate non-tenant-manager apps
        if app_label != 'tenant_manager':
            return hints.get('tenant') == db
        
        return False 