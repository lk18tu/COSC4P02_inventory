# Generated by Django 4.2.19 on 2025-04-19 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0005_alter_inventoryhistory_action'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryhistory',
            name='action',
            field=models.CharField(choices=[('add', 'Added'), ('update', 'Updated'), ('delete', 'Deleted'), ('archive', 'Archive'), ('unarchive', 'Unarchive')], max_length=10),
        ),
    ]
