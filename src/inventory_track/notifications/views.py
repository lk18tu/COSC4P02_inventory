from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Notification
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification
from django.contrib.auth.models import User

def is_admin(user):
    """Check if user is an admin."""
    return user.is_superuser

@user_passes_test(is_admin)
def send_notification(request):
    """Allows admins to send notifications to users."""
    if request.method == "POST":
        user_id = request.POST.get("user")
        message = request.POST.get("message")

        if user_id == "all":
            users = User.objects.all()
        elif user_id.isdigit():
            users = User.objects.filter(id=int(user_id))
        else:
            messages.error(request, "Invalid user selection")
            return redirect("send_notification")


        for user in users:
            Notification.objects.create(user=user, message=message)

        messages.success(request, "Notification sent successfully!")
        return redirect("dashboard")

    users = User.objects.all()
    return render(request, "notifications/send_notification.html", {"users": users})

@login_required
def view_notifications(request):

    """Displays a user's notifications."""
    print("Current user:", request.user)
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
     
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    print("User notifications:", notifications)

    return render(
        request,
        "notifications/notifications.html",
        {
            "notifications": notifications,
            "unread_notifications": unread_notifications,  
        }
    )

@login_required
def mark_notification_read(request, notification_id):
    """Marks a notification as read."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    return redirect("notifications:view_notifications")

    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, "notifications/notifications.html", {
        "notifications": notifications,
        "unread_notifications": unread_notifications,
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    return redirect("notifications:view_notifications")


