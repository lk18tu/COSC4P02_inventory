# Generated by Django 4.2.19 on 2025-02-19 20:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryApp', '0002_todoitem_quantity'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TodoItem',
            new_name='InvItem',
        ),
    ]
