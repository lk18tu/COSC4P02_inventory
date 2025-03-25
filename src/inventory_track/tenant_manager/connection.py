from django.db import connections
from django.conf import settings
import threading
import mysql.connector
from django.core.management import call_command
import sys

# Thread-local storage for the current tenant
_thread_local = threading.local()

def get_current_tenant():
    """Get the current tenant from thread-local storage"""
    return getattr(_thread_local, 'tenant', 'default')

def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage and ensure database connection exists"""
    _thread_local.tenant = tenant
    # If this is not the default tenant and not already in settings.DATABASES,
    # we need to add the database connection dynamically
    if tenant != 'default' and tenant not in settings.DATABASES:
        # Copy settings from default database and update for this tenant
        tenant_settings = settings.DATABASES['default'].copy()
        tenant_settings['NAME'] = tenant
        
        # Add all needed database configuration options
        tenant_settings['ATOMIC_REQUESTS'] = False
        tenant_settings['AUTOCOMMIT'] = True
        tenant_settings['CONN_MAX_AGE'] = 0
        
        # Add the new database connection to Django's settings
        settings.DATABASES[tenant] = tenant_settings

def create_tenant_database(db_name):
    """Create a new database for a tenant if it doesn't exist"""
    # Create MySQL connection (without specifying a database)
    conn = mysql.connector.connect(
        host=settings.DATABASES['default']['HOST'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD']
    )
    cursor = conn.cursor()
    
    # Create the database
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    
    # Close connection
    cursor.close()
    conn.close()
    
    # Add this database to Django's connections
    set_current_tenant(db_name)
    
    # Run migrations to create all necessary tables
    run_migrations_for_tenant(db_name)

def run_migrations_for_tenant(db_name):
    """Run Django migrations for a specific tenant database"""
    # Save the original stdout to restore it later
    original_stdout = sys.stdout
    sys.stdout = open('/dev/null', 'w')  # Redirect output to prevent cluttering the console
    
    try:
        # Create all tables by running migrations
        call_command('migrate', database=db_name)
    except Exception as e:
        # In case of error, print to actual stdout
        sys.stdout = original_stdout
        print(f"Error running migrations for {db_name}: {e}")
        raise
    finally:
        # Restore stdout
        sys.stdout.close()
        sys.stdout = original_stdout

def get_tenant_database_name(tenant_name):
    """Generate a database name for a tenant"""
    # Generate a unique suffix to avoid database name collisions
    import random
    import string
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"tenant_{tenant_name}_{suffix}"

# Do not try to monkey patch Django's connection directly 