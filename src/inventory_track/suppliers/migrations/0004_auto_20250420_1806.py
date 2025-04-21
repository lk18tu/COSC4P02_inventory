# suppliers/migrations/0003_drop_tracking_default.py

from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('suppliers', '0002_alter_supplyorder_created_at_and_more'),
    ]

    operations = [
        # MySQL syntax to remove any DEFAULT on tracking_number
        migrations.RunSQL(
            sql="ALTER TABLE suppliers_supplyorder ALTER tracking_number DROP DEFAULT;",
            reverse_sql="ALTER TABLE suppliers_supplyorder ALTER tracking_number SET DEFAULT NULL;"
        ),
    ]

