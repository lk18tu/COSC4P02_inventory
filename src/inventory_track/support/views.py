from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from notifications.models import Notification
from .models import SupportTicket
from django.contrib.auth.models import User

def submit_ticket(request, tenant_url=None):
    if request.method == "POST":
        username = request.POST.get("username")
        subject = request.POST.get("subject")
        description = request.POST.get("description")
        user_email = request.POST.get("email")
        user_phone = request.POST.get("phone")

        user = User.objects.filter(username=username).first()
        ticket = SupportTicket.objects.create(
            user=user if user else None,
            username=username,
            subject=subject,
            description=description,
            status="open",
            assigned_to="No one",
            notes="",
            company=tenant_url,
            user_email = user_email,
            user_phone = user_phone,
        )

        user = User.objects.filter(username=ticket.username).first()
        Notification.objects.create(
            user=user,
            message="Successfuly opened support ticket " + ticket.subject + " under " + username
        )
        return redirect(f"/{tenant_url}/support/?success=true")
       
    return render(request, 'support/new_support_ticket.html')


def supportHome(request, tenant_url=None):
    print(tenant_url)
    active_tickets = SupportTicket.objects.filter(company=tenant_url, status__in=["open", "in_progress"])
    return render(request, "support/support_home.html", {'tickets': active_tickets, 'tenant_url': tenant_url})



