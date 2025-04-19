from django.db import models

#currently not using
class InvItem(models.Model):
    title = models.CharField(max_length=250)
    completed = models.BooleanField(default=False)
    quantity = models.IntegerField()
    custom_fields = models.JSONField(default=dict)
    image = models.ImageField(upload_to='inventory_images/', null=True, blank=True) # image field
    tracking_id = models.CharField(max_length=20, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        # First, call the parent save() to ensure an ID is assigned (if new)
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # If new and tracking_id is still not set, generate it (e.g., prefix with 't')
        if is_new and not self.tracking_id:
            self.tracking_id = f"t{1000 + self.id}"
            # Update only the tracking_id field without triggering the full save again
            self.__class__.objects.filter(pk=self.pk).update(tracking_id=self.tracking_id)

def __str__(self):
    return self.title

class InvTable_Metadata(models.Model):
    table_name = models.CharField(max_length=255, unique=True)
    table_type = models.CharField(max_length=50)
    table_friendly_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, default='Default Company')

def __str__(self):
    return self.table_name
