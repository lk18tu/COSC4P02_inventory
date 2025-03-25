from django.core.management.base import BaseCommand
from tenant_manager.models import Tenant
from tenant_manager.connection import create_tenant_database, get_tenant_database_name

class Command(BaseCommand):
    help = 'Initialize a tenant database and tables'

    def add_arguments(self, parser):
        parser.add_argument('tenant_name', type=str, help='Name of the tenant to initialize')
        parser.add_argument('--company-path', type=str, help='URL path for the tenant')

    def handle(self, *args, **options):
        tenant_name = options['tenant_name']
        company_path = options.get('company_path', tenant_name)
        
        # Generate the database name
        db_name = get_tenant_database_name(tenant_name)
        
        # Create the database and run migrations
        try:
            self.stdout.write(f"Creating database {db_name}...")
            create_tenant_database(db_name)
            self.stdout.write(self.style.SUCCESS(f"Successfully created and initialized database {db_name}"))
            
            # Create the tenant record
            tenant, created = Tenant.objects.get_or_create(
                name=tenant_name,
                db_name=db_name,
                company_path=company_path
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created tenant record for {tenant_name}"))
            else:
                self.stdout.write(f"Tenant record for {tenant_name} already exists")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error initializing tenant: {e}")) 