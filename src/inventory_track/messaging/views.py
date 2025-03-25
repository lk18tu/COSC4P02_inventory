from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Message, Contact
from django.contrib.auth.models import User
from django.contrib import messages

@login_required
def send_message(request):
    """Allows users to send messages by username, email, or contact selection."""
    if request.method == "POST":
        recipient_input = request.POST.get("recipient").strip()
        subject = request.POST.get("subject", "").strip()
        content = request.POST.get("content").strip()

        if not recipient_input:
            messages.error(request, "Recipient cannot be empty.")
            return redirect("messaging:send_message")

        try:
            # Determine if the input is an email
            if "@" in recipient_input:
                matched_users = User.objects.filter(email=recipient_input)
                if matched_users.count() == 1:
                    recipient = matched_users.first()
                elif matched_users.count() > 1:
                    messages.error(request, "Multiple users found for this email. Please enter username.")
                    return redirect("messaging:send_message")
                else:
                    messages.error(request, "No user found with this email.")
                    return redirect("messaging:send_message")
            else:
                recipient = User.objects.get(username=recipient_input)

            # Create and send message
            Message.objects.create(sender=request.user, recipient=recipient, subject=subject, content=content)
            messages.success(request, f"Message sent to {recipient.username}.")
            return redirect("messaging:inbox")

        except User.DoesNotExist:
            messages.error(request, "Recipient not found.")
            return redirect("messaging:send_message")

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

# Add Contacts
@login_required
def contacts_view(request):
    """Handles contact list: display, add, and manage contacts."""
    contacts = Contact.objects.filter(user=request.user)
    candidates = []

    if request.method == "POST":
        # Case 1: user selects one username from email match result
        if "selected_username" in request.POST:
            selected_username = request.POST.get("selected_username").strip()
            try:
                selected_user = User.objects.get(username=selected_username)

                if selected_user == request.user:
                    messages.error(request, "You cannot add yourself as a contact.")
                elif Contact.objects.filter(user=request.user, contact=selected_user).exists():
                    messages.warning(request, "This contact is already in your list.")
                else:
                    Contact.objects.create(user=request.user, contact=selected_user)
                    messages.success(request, f"{selected_username} has been added to your contacts.")
            except User.DoesNotExist:
                messages.error(request, "Selected user no longer exists.")

            return redirect("messaging:contacts")

        # Case 2: user inputs raw username or email
        raw_input = request.POST.get("contact").strip()
        if not raw_input:
            messages.error(request, "Input cannot be empty.")
            return redirect("messaging:contacts")

        # Determine if input is email
        if "@" in raw_input:
            matched_users = User.objects.filter(email=raw_input)
            if matched_users.count() == 1:
                matched_user = matched_users.first()
                if matched_user == request.user:
                    messages.error(request, "You cannot add yourself as a contact.")
                elif Contact.objects.filter(user=request.user, contact=matched_user).exists():
                    messages.warning(request, "This contact is already in your list.")
                else:
                    Contact.objects.create(user=request.user, contact=matched_user)
                    messages.success(request, f"{matched_user.username} has been added to your contacts.")
            elif matched_users.count() > 1:
                # Show list of usernames to select
                candidates = matched_users
            else:
                messages.error(request, "No users found with this email.")
        else:
            try:
                user = User.objects.get(username=raw_input)
                if user == request.user:
                    messages.error(request, "You cannot add yourself as a contact.")
                elif Contact.objects.filter(user=request.user, contact=user).exists():
                    messages.warning(request, "This contact is already in your list.")
                else:
                    Contact.objects.create(user=request.user, contact=user)
                    messages.success(request, f"{user.username} has been added to your contacts.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")

    return render(request, "messaging/contacts.html", {
        "contacts": contacts,
        "candidates": candidates,
    })

@login_required
def delete_contact(request, contact_id):
    """Allows user to remove a contact."""
    contact = Contact.objects.get(id=contact_id, user=request.user)
    contact.delete()
    return redirect("messaging:contacts")