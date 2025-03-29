from django.db import connections
from contextlib import contextmanager

@contextmanager
def tenant_context(tenant):
    """
    Context manager to use a tenant-specific database connection.
    """
    # Ensure the connection exists
    connections.ensure_defaults(tenant.schema_name)
    if tenant.schema_name not in connections.databases:
        connections.databases[tenant.schema_name] = {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': tenant.schema_name,
            'USER': connections.databases['default']['USER'],
            'PASSWORD': connections.databases['default']['PASSWORD'],
            'HOST': connections.databases['default']['HOST'],
            'PORT': connections.databases['default']['PORT'],
        }
    
    # Use the tenant-specific connection
    old_default = connections.databases['default']
    connections.databases['default'] = connections.databases[tenant.schema_name]
    
    try:
        yield
    finally:
        # Restore the original default connection
        connections.databases['default'] = old_default
