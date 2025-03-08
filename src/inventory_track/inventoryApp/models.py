from django.db import models

# Create your models here.

class InvItem(models.Model):
    title = models.CharField(max_length=250)
    completed = models.BooleanField(default=False)
    quantity = models.IntegerField()
    custom_fields = models.JSONField(default=dict)  # Stores custom fields as a JSON object

    

    def __str__(self):
        return self.title
    


class InvTable_Metadata(models.Model):
    table_name = models.CharField(max_length=255, unique=True)
    table_type = models.CharField(max_length=50)
    table_location = models.CharField(max_length=255)



    def __str__(self):
        return self.table_name