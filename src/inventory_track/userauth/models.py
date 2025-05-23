# userauth/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('employee', 'Employee'),
        ('manager', 'Manager'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='employee',
    )

    def is_manager(self):
        return self.user_type == 'manager'

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

class PendingRegistration(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Will store hashed password
    tenant_url = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Pending: {self.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_as_read(self):
        self.is_read = True
        self.save()
