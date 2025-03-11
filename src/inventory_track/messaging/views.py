from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Message, Contact
from django.contrib.auth.models import User

@login_required
def send_message(request):
    """Allows users to send messages to other registered users."""
    if request.method == "POST":
        recipient_username = request.POST.get("recipient")
        subject = request.POST.get("subject")
        content = request.POST.get("content")

        recipient = User.objects.get(username=recipient_username)
        Message.objects.create(sender=request.user, recipient=recipient, subject=subject, content=content)

        return redirect("messaging:inbox")

    contacts = Contact.objects.filter(user=request.user)
    return render(request, "messaging/send_message.html", {"contacts": contacts})

# View Inbox
@login_required
def inbox(request):
    """Displays all received messages for the logged-in user."""
    messages = Message.objects.filter(recipient=request.user).order_by("-timestamp")
    return render(request, "messaging/inbox.html", {"messages": messages})

# Read a Message
@login_required
def read_message(request, message_id):
    """Displays a single message and marks it as read."""
    message = Message.objects.get(id=message_id, recipient=request.user)
    message.mark_as_read()
    return render(request, "messaging/read_message.html", {"message": message})
