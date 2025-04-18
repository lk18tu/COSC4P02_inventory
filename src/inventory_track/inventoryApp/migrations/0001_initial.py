# Generated by Django 5.1.5 on 2025-04-18 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InvItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250)),
                ('completed', models.BooleanField(default=False)),
                ('quantity', models.IntegerField()),
                ('custom_fields', models.JSONField(default=dict)),
                ('image', models.ImageField(blank=True, null=True, upload_to='inventory_images/')),
                ('tracking_id', models.CharField(blank=True, max_length=20, null=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='InvTable_Metadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('table_name', models.CharField(max_length=255, unique=True)),
                ('table_type', models.CharField(max_length=50)),
                ('table_friendly_name', models.CharField(max_length=255)),
            ],
        ),
    ]
