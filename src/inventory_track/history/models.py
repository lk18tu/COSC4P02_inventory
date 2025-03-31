from django.db import models
from django.contrib.auth.models import User
from inventoryApp.models import InvItem

class InventoryHistory(models.Model):
    ACTION_CHOICES = [
        ('add', 'Added'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
    ]

    item = models.ForeignKey(InvItem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.item.title} - {self.get_action_display()} by {self.user.username if self.user else 'Unknown'} at {self.timestamp}"
