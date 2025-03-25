from django.core.management import call_command
from django.db import connections
import os
from django.conf import settings
import subprocess

def initialize_tenant_database(db_name):
    """
    Initialize a new tenant database with required tables
    """
    # Get a connection to the tenant database
    connection = connections[db_name]
    
    # List of apps to migrate (excluding tenant_manager)
    apps_to_migrate = [
        'auth',
        'contenttypes',
        'sessions',
        'admin',
        'userauth',
        'messaging',
        'updateStock',
        'manager',
        'notifications',
        'inventoryApp',
        'inventory_analysis',
        'history',
        'suppliers',
    ]
    
    # Create database tables for each app
    for app in apps_to_migrate:
        # Use Django's management command to create tables
        try:
            call_command('migrate', app, database=db_name)
        except Exception as e:
            print(f"Error migrating {app}: {str(e)}")
    
    # Create superuser for the tenant (optional)
    # This would require custom code as call_command for createsuperuser
    # requires interactive input
