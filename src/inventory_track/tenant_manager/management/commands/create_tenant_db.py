from django.core.management.base import BaseCommand
from django.db import connection
from tenant_manager.models import Tenant

class Command(BaseCommand):
    help = 'Creates database schemas for all tenants'

    def handle(self, *args, **options):
        tenants = Tenant.objects.all()
        
        for tenant in tenants:
            self.stdout.write(f"Creating database for tenant: {tenant.name}")
            
            try:
                with connection.cursor() as cursor:
                    # Create the database if it doesn't exist
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {tenant.schema_name}")
                    
                self.stdout.write(self.style.SUCCESS(f"Successfully created database for {tenant.name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error creating database for {tenant.name}: {str(e)}"))
