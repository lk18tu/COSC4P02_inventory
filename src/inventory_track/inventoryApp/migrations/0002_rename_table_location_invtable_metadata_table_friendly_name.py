# Generated by Django 4.2.19 on 2025-04-04 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryApp', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='invtable_metadata',
            old_name='table_location',
            new_name='table_friendly_name',
        ),
    ]
