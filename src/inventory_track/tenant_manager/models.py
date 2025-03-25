from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Tenant(models.Model):
    """Model representing a company tenant"""
    name = models.CharField(max_length=100)
    db_name = models.CharField(max_length=100, unique=True)
    company_path = models.CharField(max_length=100, unique=True, default='default')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_tenants', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
