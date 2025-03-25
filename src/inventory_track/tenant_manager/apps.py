from django.apps import AppConfig


class TenantManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenant_manager'

    def ready(self):
        # Import connection handling
        import tenant_manager.connection
