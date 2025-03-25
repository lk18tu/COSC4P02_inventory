from django.db import models

class InvTable_Metadata(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class InvItem(models.Model):
    table_name = models.CharField(max_length=255)
    item_id = models.IntegerField(default=1)
    product_number = models.CharField(max_length=100, blank=True, null=True)
    upc = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    quantity_stock = models.IntegerField(blank=True, null=True)
    reorder_level = models.IntegerField(blank=True, null=True)
    price = models.FloatField(blank=True, null=True)
    purchase_price = models.FloatField(blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)  # Changed from ImageField for simplicity
    notes = models.TextField(blank=True, null=True)
    custom_fields = models.JSONField(default=dict)
    
    class Meta:
        unique_together = ('table_name', 'item_id')
        
    def __str__(self):
        return f"{self.table_name} - {self.title}"
