# src/inventory_track/messaging/forms.py

from django import forms
from django.contrib.auth.models import User

class MessageForm(forms.Form):
    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter username or email'})
    )
    subject = forms.CharField(required=False)
    content = forms.CharField(widget=forms.Textarea, required=True)
