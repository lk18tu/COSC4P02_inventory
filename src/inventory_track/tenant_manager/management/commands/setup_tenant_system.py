from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Sets up the initial database structure for the tenant system'

    def handle(self, *args, **options):
        self.stdout.write("Setting up the tenant system...")
        
        try:
            with connection.cursor() as cursor:
                # Create the tenant_manager_tenant table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `tenant_manager_tenant` (
                        `id` int(11) NOT NULL AUTO_INCREMENT,
                        `name` varchar(100) NOT NULL,
                        `schema_name` varchar(100) NOT NULL,
                        `domain_url` varchar(128) NOT NULL,
                        `created_on` datetime(6) NOT NULL,
                        `is_active` tinyint(1) NOT NULL,
                        `owner_id` int(11) NOT NULL,
                        PRIMARY KEY (`id`),
                        UNIQUE KEY `name` (`name`),
                        UNIQUE KEY `schema_name` (`schema_name`),
                        UNIQUE KEY `domain_url` (`domain_url`),
                        KEY `tenant_manager_tenant_owner_id` (`owner_id`),
                        CONSTRAINT `tenant_manager_tenant_owner_id_fk` FOREIGN KEY (`owner_id`) 
                        REFERENCES `auth_user` (`id`)
                    )
                """)
                
                self.stdout.write(self.style.SUCCESS("Successfully set up the tenant system"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error setting up the tenant system: {str(e)}"))
