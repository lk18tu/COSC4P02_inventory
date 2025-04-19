import uuid
from django.db import models
from inventoryApp.models import InvTable_Metadata

class StockTransaction(models.Model):
    table_meta     = models.ForeignKey(
        InvTable_Metadata,
        on_delete=models.CASCADE,
        help_text="Which inventory class this transaction belongs to"
    )
    item_id        = models.IntegerField(
        help_text="The id of the row in the class table"
    )
    change         = models.IntegerField(
        help_text="Positive for add, negative for remove"
    )
    tracking_id    = models.CharField(
        max_length=255,
        help_text="Unique identifier for each physical unit (reused in tx log)",
        db_index=True
    )
    transaction_id = models.CharField(
        max_length=36,
        default=uuid.uuid4,
        help_text="UUID for this transaction event",
        db_index=True
    )
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [ models.Index(fields=["table_meta", "item_id"]) ]

    def __str__(self):
        sign = "+" if self.change>0 else ""
        return f"{self.table_meta.table_name}•{self.item_id} {sign}{self.change} (unit={self.tracking_id})"


class StockUnit(models.Model):
    """
    The *current* state of each physical unit.
    """
    table_meta      = models.ForeignKey(
        InvTable_Metadata,
        on_delete=models.CASCADE
    )
    item_id         = models.IntegerField(
        help_text="Which master row this unit belongs to"
    )
    tracking_id     = models.CharField(
        max_length=255,
        primary_key=True,
        help_text="Unique identifier for this physical unit"
    )
    status          = models.CharField(
        max_length=50,
        default="In Stock",
        help_text="e.g. In Stock, Removed, Damaged…"
    )
    location        = models.CharField(
        max_length=100,
        default="Warehouse",
        help_text="Where it lives right now"
    )

    class Meta:
        indexes = [
            models.Index(fields=["table_meta", "item_id"]),
        ]
        unique_together = [
            ("table_meta", "item_id", "tracking_id"),
        ]

    def __str__(self):
        return f"{self.tracking_id} ({self.status}@{self.location})"
