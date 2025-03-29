from django.db import models
from inventoryApp.models import InvItem


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    

    def __str__(self):
        return self.name


class SupplyOrder(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='supply_orders')
    order_date = models.DateField()
    status = models.CharField(max_length=50, choices=[('PENDING', 'Pending'), ('RECEIVED', 'Received')], default='PENDING')

    def __str__(self):
        return f"Order from {self.supplier.name} on {self.order_date}"
    
    def mark_as_received(self):
        self.status = 'RECEIVED'
        self.save()
        # Update inventory levels
        for item_line in self.order_items.all():
            inventory_item = item_line.inventory_item
            inventory_item.quantity += item_line.quantity
            inventory_item.save()

class SupplyOrderItem(models.Model):
    supply_order = models.ForeignKey(SupplyOrder, on_delete=models.CASCADE, related_name='order_items')
    inventory_item = models.ForeignKey(InvItem, on_delete=models.CASCADE)
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.quantity} of {self.inventory_item.title} for {self.supply_order}"