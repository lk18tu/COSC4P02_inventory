from django.db import models
from django.contrib.auth.models import User

class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact = models.ForeignKey(User, related_name="contact_user", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} -> {self.contact.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def mark_as_read(self):
        self.read = True
        self.save()

    def __str__(self):
        return f"From {self.sender} to {self.recipient}: {self.subject}"
