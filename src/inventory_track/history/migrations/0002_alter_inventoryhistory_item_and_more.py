# Generated by Django 4.2.19 on 2025-03-23 03:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('history', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventoryhistory',
            name='item',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='inventoryhistory',
            name='user',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
