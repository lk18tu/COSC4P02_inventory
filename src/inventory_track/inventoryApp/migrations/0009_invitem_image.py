# Generated by Django 5.1.5 on 2025-03-11 13:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventoryApp', '0008_alter_invtable_metadata_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitem',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='inventory_images/'),
        ),
    ]
