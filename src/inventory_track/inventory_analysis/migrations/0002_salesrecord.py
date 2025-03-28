# Generated by Django 5.1.5 on 2025-03-09 21:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory_analysis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SalesRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_sold', models.IntegerField()),
                ('date', models.DateField(auto_now_add=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory_analysis.inventoryitem')),
            ],
        ),
    ]
