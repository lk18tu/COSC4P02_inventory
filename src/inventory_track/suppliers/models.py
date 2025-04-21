import uuid
from django.db import models, connection
from django.db.models import F
from django.utils import timezone
from inventoryApp.models import InvTable_Metadata
from inventoryApp.models import InvItem


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class SupplyOrder(models.Model):
    STATUS_CHOICES = [
        ('AT_SUPPLIER', 'At Supplier'),
        ('IN_TRANSIT', 'In Transit'),
        ('RECEIVED', 'Received'),
    ]

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='AT_SUPPLIER'
    )
    destination_percentage = models.PositiveIntegerField(default=0)
    location_name = models.CharField(
        max_length=255,
        default='Unknown',      
    )
    tracking_number = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        help_text='Auto-generated order tracking number',
    )
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="Time this order was created",  
        editable=False, 
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.tracking_number} for {self.supplier.name}"

    def _ensure_inventory_tables(self):
        prefix = f"{self.supplier.name}_{self.location_name}".lower().replace(" ", "_")
        classes_table = f"{prefix}_classes"
        items_table   = f"{prefix}_items"

        with connection.cursor() as cursor:
           
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{classes_table}` (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255),
                    product_number VARCHAR(255)
                ) ENGINE=InnoDB;
            """)

            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{items_table}` (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    inventory_item_id BIGINT NOT NULL,
                    tracking_number VARCHAR(32) UNIQUE NOT NULL,
                    destination_percentage INT UNSIGNED NOT NULL
                ) ENGINE=InnoDB;
            """)

        
        InvTable_Metadata.objects.get_or_create(
            table_name=classes_table,
            defaults={
                'table_type': 'inventory',
                'table_friendly_name': self.location_name,
                'company_name': self.supplier.name,
            }
        )
        InvTable_Metadata.objects.get_or_create(
            table_name=items_table,
            defaults={
                'table_type': 'inventory_individual_items',
                'table_friendly_name': self.location_name,
                'company_name': self.supplier.name,
            }
        )

        return items_table, classes_table
    
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        if not self.tracking_number:
             self.tracking_number = uuid.uuid4().hex.upper()
        super().save(*args, **kwargs)
 
        if is_new:
             self._ensure_inventory_tables()


    def receive(self):
        """
        Mark this order as received and insert each line-item into
        the proper per-location items table with unique tracking IDs.
        """
        if self.status == 'RECEIVED':
            return
        self.status = 'RECEIVED'
        self.save()

        
        items_table, _ = self._ensure_inventory_tables()

        with connection.cursor() as cursor:
            for line in self.order_items.select_related('inventory_item'):
                for _ in range(line.quantity):
                  unit_tracking = uuid.uuid4().hex.upper()
                  cursor.execute(f"""
                        INSERT INTO `{items_table}`
                        (inventory_item_id, tracking_number, destination_percentage)
                       VALUES (%s, %s, %s);
            """, [
                line.inventory_item.id,
                unit_tracking,
                self.destination_percentage
            ])

        # Increment the overall InvItem.quantity by the number ordered
        # so the main inventory stays in sync.
        for line in self.order_items.all():
            InvItem.objects.filter(pk=line.inventory_item_id).update(
                quantity=F('quantity') + line.quantity
            )

class SupplyOrderItem(models.Model):
    supply_order = models.ForeignKey(
        SupplyOrder,
        on_delete=models.CASCADE,
        related_name='order_items'
    )
    inventory_item = models.ForeignKey(
        'inventoryApp.InvItem',
        on_delete=models.CASCADE,
        help_text="Which product is being ordered"
    )
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity}× {self.inventory_item.title}"
