class TenantRouter:
    """
    A router to control database operations for tenant-specific models.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read tenant models go to the tenant's database.
        """
        if hasattr(hints.get('instance', None), 'tenant'):
            return hints['instance'].tenant.schema_name
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write tenant models go to the tenant's database.
        """
        if hasattr(hints.get('instance', None), 'tenant'):
            return hints['instance'].tenant.schema_name
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the same database.
        """
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the tenant models only appear in the tenant databases.
        """
        return True
