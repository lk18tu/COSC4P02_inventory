from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Notification(models.Model):
    """Model for storing notifications for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    created_at = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)

    def mark_as_read(self):
        """Marks a notification as read."""
        self.is_read = True
        self.save()

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"
