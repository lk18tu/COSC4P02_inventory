from django.db import models
from django.contrib.auth.models import User
from inventoryApp.models import InvItem

class InventoryHistory(models.Model):
    ACTION_CHOICES = [
        ('add', 'Added'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('archive', 'Archive'),
        ('unarchive', 'Unarchive'),
    ]

    location = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)
    item_class_number = models.IntegerField(null=True, blank=True, default=-1)
    individual_item_number = models.IntegerField(null=True, blank=True, default=-1)

    def __str__(self):
        return f"{self.item.title} - {self.get_action_display()} by {self.user.username if self.user else 'Unknown'} at {self.timestamp}"
