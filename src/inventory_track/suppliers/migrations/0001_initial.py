# Generated by Django 5.1.5 on 2025-04-19 13:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventoryApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=50, null=True)),
                ('address', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SupplyOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_date', models.DateField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('RECEIVED', 'Received')], default='PENDING', max_length=50)),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supply_orders', to='suppliers.supplier')),
            ],
        ),
        migrations.CreateModel(
            name='SupplyOrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField()),
                ('inventory_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventoryApp.invitem')),
                ('supply_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_items', to='suppliers.supplyorder')),
            ],
        ),
    ]
