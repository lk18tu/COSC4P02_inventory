from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from tenant_manager.models import Tenant

class Command(BaseCommand):
    help = 'Initialize a tenant database with tables and initial data'

    def add_arguments(self, parser):
        parser.add_argument('tenant_id', type=int, help='ID of the tenant to initialize')

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant with ID {tenant_id} does not exist"))
            return
            
        self.stdout.write(f"Initializing database for tenant: {tenant.name}")
        
        try:
            # Create a connection to the tenant database
            connections.ensure_defaults(tenant.schema_name)
            connections.databases[tenant.schema_name] = {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': tenant.schema_name,
                'USER': connections.databases['default']['USER'],
                'PASSWORD': connections.databases['default']['PASSWORD'],
                'HOST': connections.databases['default']['HOST'],
                'PORT': connections.databases['default']['PORT'],
            }
            
            # Run migrations on the tenant database
            call_command('migrate', database=tenant.schema_name)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully initialized database for {tenant.name}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error initializing database for {tenant.name}: {str(e)}"))
