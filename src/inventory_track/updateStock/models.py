import uuid
from django.db import models
from inventoryApp.models import InvTable_Metadata

class StockTransaction(models.Model):
    table_meta = models.ForeignKey(
        InvTable_Metadata,
        on_delete=models.CASCADE,
        help_text="Which inventory class this transaction belongs to"
    )
    item_id = models.IntegerField(
        help_text="The id of the row in the class table"
    )
    change = models.IntegerField(
        help_text="Positive for add, negative for remove"
    )
    # Unique per‐unit ID (never reused, survives removals)
    tracking_id = models.CharField(
        max_length=255,
        help_text="Unique identifier for each physical unit (can appear multiple times in transactions)",
        db_index=True
    )
    # Unique per action (same UUID for a bulk add or removal batch)
    transaction_id = models.CharField(
        max_length=36,
        default=uuid.uuid4,
        help_text="UUID for this transaction event",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["table_meta", "item_id"]),
        ]

    def __str__(self):
        sign = "+" if self.change > 0 else ""
        return (
            f"{self.table_meta.table_name}•{self.item_id} "
            f"{sign}{self.change}  "
            f"(unit={self.tracking_id}, tx={self.transaction_id})"
        )