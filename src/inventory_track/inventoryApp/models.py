from django.db import models

# Create your models here.

class InvItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    quantity = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    