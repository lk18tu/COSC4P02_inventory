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
from notifications.models import Notification
from django.contrib.auth.models import User

def is_admin(user):
    """Check if user is an admin."""
    return user.is_superuser

@user_passes_test(is_admin)
def send_notification(request, tenant_url=None):
    """Allows admins to send notifications to users."""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == "POST":
        user_id = request.POST.get("user")
        message = request.POST.get("message")

        if user_id == "all":
            users = User.objects.all()
        elif user_id.isdigit():
            users = User.objects.filter(id=int(user_id))
        else:
            messages.error(request, "Invalid user selection")
            return redirect("notifications:send_notification", tenant_url=tenant_url)

        for user in users:
            Notification.objects.create(user=user, message=message)

        messages.success(request, "Notification sent successfully!")
        return redirect("dashboard", tenant_url=tenant_url)

    users = User.objects.all()
    return render(request, "notifications/send_notification.html", {
        "users": users,
        "tenant_url": tenant_url,
    })

@login_required
def view_notifications(request, tenant_url=None):
    """Displays a user's notifications."""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
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
            "tenant_url": tenant_url,  # Add tenant_url to the context
        }
    )

@login_required
def mark_notification_read(request, notification_id, tenant_url=None):
    """Marks a notification as read."""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    if request.is_ajax():
        return JsonResponse({
            "unread_notifications": unread_notifications
        })
    
    return redirect("notifications:view_notifications", tenant_url=tenant_url)


