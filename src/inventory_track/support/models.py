from django.db import models
from django.contrib.auth.models import User

class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150, blank=True) 
    user_email = models.CharField(max_length=255, default="default")
    user_phone = models.CharField(max_length=255, default="default")
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.CharField(max_length=255, default="defautl")
    assigned_to = models.CharField(max_length=255)
    notes = models.TextField()


    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"