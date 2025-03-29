### tenant_manager/management/commands/tenant_createsuperuser.py


from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from userauth.models import UserProfile
from tenant_manager.models import Tenant
from tenant_manager.utils import tenant_context

class Command(BaseCommand):
    help = 'Creates a superuser for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument('tenant_id', type=int, help='ID of the tenant')
        parser.add_argument('username', type=str, help='Username for the superuser')
        parser.add_argument('email', type=str, help='Email for the superuser')
        parser.add_argument('password', type=str, help='Password for the superuser')

    def handle(self, *args, **options):
        tenant_id = options['tenant_id']
        username = options['username']
        email = options['email']
        password = options['password']
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant with ID {tenant_id} does not exist"))
            return
            
        self.stdout.write(f"Creating superuser for tenant: {tenant.name}")
        
        try:
            with tenant_context(tenant):
                # Create the superuser
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Create a manager profile for the superuser
                UserProfile.objects.create(user=user, user_type='manager')
                
                self.stdout.write(self.style.SUCCESS(f"Successfully created superuser {username} for tenant {tenant.name}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating superuser: {str(e)}"))

