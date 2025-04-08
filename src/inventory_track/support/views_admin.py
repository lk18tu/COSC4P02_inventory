from django.shortcuts import get_object_or_404, render, redirect
from .models import SupportTicket
from notifications.models import Notification
from django.contrib.auth.models import User

# Dummy hardcoded admin login (replace later with real auth)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"

def support_admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            request.session["is_support_admin"] = True  # Store login session
            return redirect("support_admin:support_admin_dashboard")
    return render(request, "support/admin_login.html")

def support_admin_dashboard(request):
    # 🔴 Prevent access if not logged in
    if not request.session.get("is_support_admin"):
        return redirect("support_admin:support_admin_login")  # Redirect to login page

    tickets = SupportTicket.objects.all()
    return render(request, "support/admin_dashboard.html", {"tickets": tickets})

def support_admin_logout(request):
    request.session.pop("is_support_admin", None)  # Clear session
    return redirect("support_admin:support_admin_login")

def update_ticket(request, ticket_id):
    ticket = get_object_or_404(SupportTicket, id=ticket_id)

    
    
    if request.method == "POST":
        ticket.status = request.POST.get("status")
        ticket.notes = request.POST.get("notes")
        ticket.assigned_to = request.POST.get("assigned_to")
        ticket.save()


        if(ticket.status == "closed"):

            user = User.objects.filter(username=ticket.username).first()
            Notification.objects.create(
                user=user,
                message="Your ticket " + ticket.subject + " #" + str(ticket_id) + " has been closed by support"
            )


        
    return redirect("support_admin:support_admin_dashboard")