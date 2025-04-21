# userauth/views.py
import pytz
import datetime
import logging
import re

from django.db import connection
from django.db.models import Sum, Count

from django.conf import settings
from django.shortcuts import render, redirect

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User

from .models import UserProfile, PendingRegistration, Notification
from notifications.models import Notification  # Import Notification from the notifications app

from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password

from inventory_analysis.views import (
    get_available_inventory_tables,
    generate_inventory_level_chart
)
from inventoryApp.models import InvTable_Metadata
from updateStock.models import StockTransaction



logger = logging.getLogger(__name__)

# check if user is a manager
def manager_required(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.is_manager()

def register(request, tenant_url=None):
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        # Debug: print the POST data to see what's being submitted
        print("POST data:", request.POST)
        
        # Get form data using the field names from the modal
        username = request.POST.get('username', '')
        email = request.POST.get('email', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '') 
        
        # Check if this is an AJAX request (from modal)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Validate form data
        if not username or not email or not password1:
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'All fields are required'})
            messages.error(request, 'All fields are required')
        elif password2 and password1 != password2:
            # If password2 exists and doesn't match password1
            if is_ajax:
                return JsonResponse({'status': 'error', 'message': 'Passwords do not match'})
            messages.error(request, 'Passwords do not match')
        else:
            if User.objects.filter(username=username).exists():
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'User already exists'})
                messages.error(request, 'User already exists')
            elif User.objects.filter(email=email).exists():
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'Email already exists'})
                messages.error(request, 'Email already exists')
            elif PendingRegistration.objects.filter(username=username).exists():
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'Registration with this username is already pending approval'})
                messages.error(request, 'Registration with this username is already pending approval')
            elif PendingRegistration.objects.filter(email=email).exists():
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': 'Registration with this email is already pending approval'})
                messages.error(request, 'Registration with this email is already pending approval')
            else:
                # Check if there are any managers in the system already
                managers_exist = UserProfile.objects.filter(user_type='manager').exists()
                
                if not managers_exist:
                    # If no managers exist, create the user as a manager directly
                    user = User.objects.create_user(username=username, email=email, password=password1)
                    UserProfile.objects.create(user=user, user_type='manager')
                    
                    # Log the user in automatically
                    login(request, user)
                    
                    messages.success(request, 'Registration successful - You are now the manager of this company')
                    
                    if is_ajax:
                        return JsonResponse({
                            'status': 'success', 
                            'message': 'Registration successful - You are now the manager of this company',
                            'redirect_url': f'/{tenant_url}/userauth/dashboard/'
                        })
                    
                    # Redirect directly to dashboard
                    return redirect(f'/{tenant_url}/userauth/dashboard/')
                else:
                    # Create a pending registration for managers to approve
                    hashed_password = make_password(password1)
                    PendingRegistration.objects.create(
                        username=username,
                        email=email,
                        password=hashed_password,
                        tenant_url=tenant_url
                    )
                    
                    # Notify all managers about the new registration
                    manager_users = User.objects.filter(profile__user_type='manager')
                    for manager in manager_users:
                        Notification.objects.create(
                            user=manager,
                            message=f"New registration request from {username} is pending approval"
                        )
                    
                    messages.success(request, 'Registration submitted successfully. Your account is awaiting manager approval.')
                    
                    if is_ajax:
                        return JsonResponse({
                            'status': 'success', 
                            'message': 'Registration submitted successfully. Your account is awaiting manager approval.',
                            'redirect_url': f'/{tenant_url}/'
                        })
                    
                    # Redirect to tenant landing page
                    return redirect(f'/{tenant_url}/')
    
    # For GET requests, this should never be called if the template is deprecated
    return redirect(f'/{tenant_url}/')

def user_login(request, tenant_url=None):
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Check if this user has a pending registration
        pending = PendingRegistration.objects.filter(username=username).exists()
        if pending:
            if is_ajax:
                return JsonResponse({
                    'status': 'pending',
                    'message': 'Your registration is pending approval by a manager.',
                    'username': username
                })
            messages.warning(request, 'Your registration is pending approval by a manager.')
            return redirect(f'/{tenant_url}/')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # profile exists (for existing users)
            UserProfile.objects.get_or_create(user=user)
            
            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': f'/{tenant_url}/userauth/dashboard/'
                })
            
            return redirect(f'/{tenant_url}/userauth/dashboard/')
        else:
            if is_ajax:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username or password does not match'
                })
            messages.error(request, 'Username or password does not match')
            return redirect(f'/{tenant_url}/')
    
    # For GET requests
    return redirect(f'/{tenant_url}/')

def user_logout(request, tenant_url=None):
    """Logs out the user and redirects to the tenant landing page."""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    logout(request)
    # Redirect to the tenant landing page instead of the login page
    return redirect(f'/{tenant_url}/')

@login_required
def dashboard(request, tenant_url=None):
    # resolve tenant_url
    tenant_url = (
        request.tenant.domain_url
        if hasattr(request, "tenant")
        else (tenant_url or "")
    )

    # 1) list of all inventory tables & which one’s selected
    inventory_tables = get_available_inventory_tables()
    selected_table = request.GET.get("table") or (
        inventory_tables[0] if inventory_tables else None
    )

    # build a friendly label for each table, e.g. "Table1" → "Table 1"
    table_options = []
    for tbl in inventory_tables:
        # drop the suffix (_classes) and tenant prefix
        base = tbl.rsplit("_", 1)[0]  # e.g. "Test_company_1_Table1"
        raw = base.split("_")[-1]     # e.g. "Table1"
        label = re.sub(r"([A-Za-z]+)(\d+)", r"\1 \2", raw)
        table_options.append({"name": tbl, "label": label})

    # 2) KPI metrics
    total_skus = total_units = items_below = 0
    avg_daily_sell = 0.0

    if selected_table:
        with connection.cursor() as cursor:
            # total distinct SKUs
            cursor.execute(f"SELECT COUNT(*) FROM `{selected_table}`")
            total_skus = cursor.fetchone()[0] or 0

            # total units in stock
            cursor.execute(f"SELECT SUM(quantity_stock) FROM `{selected_table}`")
            total_units = cursor.fetchone()[0] or 0

            # items below reorder level
            cursor.execute(
                f"SELECT COUNT(*) FROM `{selected_table}` "
                "WHERE quantity_stock < reorder_level"
            )
            items_below = cursor.fetchone()[0] or 0

            # average daily sell‑through over last 7 days
            cursor.execute(
                """
                SELECT ABS(SUM(`change`))
                  FROM updatestock_stocktransaction
                 WHERE table_meta_id = (
                         SELECT id
                           FROM inventoryapp_invtable_metadata
                          WHERE table_name = %s
                       )
                   AND item_id IN (SELECT id FROM `{tbl}`)
                   AND `change` < 0
                   AND created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """.replace("{tbl}", selected_table),
                [selected_table],
            )
            removed_last_week = cursor.fetchone()[0] or 0
            avg_daily_sell = round(removed_last_week / 7, 1)

    # 3) bar chart for selected table
    inventory_bar_chart = (
        generate_inventory_level_chart(selected_table)
        if selected_table else None
    )

    # 3.5) build reorder‐progress list
    progress_items = []
    if selected_table:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT title, quantity_stock, reorder_level "
                f"FROM `{selected_table}`"
            )
            for title, qty, rl in cursor.fetchall():
                pct = int((qty / rl * 100) if rl and rl > 0 else 0)
                pct = min(pct, 100)
                progress_items.append({"title": title, "pct": pct})

    # 4) time, notifications & user type
    eastern = pytz.timezone("US/Eastern")
    now = datetime.datetime.now(eastern)
    formatted_date_time = now.strftime("%B %d, %Y, %I:%M %p EST")

    UserProfile.objects.get_or_create(user=request.user)

    # fetch last 5 notifications
    notifications = (
        Notification.objects
                    .filter(user=request.user)
                    .order_by("-created_at")[:5]
    )
    unread = (
        Notification.objects
                    .filter(user=request.user, is_read=False)
                    .count() or 0
    )

    return render(request, "userauth/dashboard.html", {
        "tenant_url":           tenant_url,
        "current_time":         formatted_date_time,
        "is_manager":           request.user.profile.is_manager(),
        "unread_notifications": unread,

        "inventory_tables":     inventory_tables,
        "table_options":        table_options,
        "selected_table":       selected_table,
        "inventory_bar_chart":  inventory_bar_chart,

        # KPI context
        "total_skus":           total_skus,
        "total_units":          total_units,
        "items_below":          items_below,
        "percent_below":        (round(items_below / total_skus * 100, 1)
                                   if total_skus else 0),
        "avg_daily_sell":       avg_daily_sell,

        # Reorder progress
        "progress_items":       progress_items,

        # Notifications
        "notifications":        notifications,
    })



class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'userauth/password_reset.html'
    email_template_name = 'userauth/password_reset_email.html'
    subject_template_name = 'userauth/password_reset_subject.txt'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        form.save(
            request=self.request,
            use_https=True if settings.PROTOCOL == 'https' else False,
            from_email=settings.EMAIL_HOST_USER,
            email_template_name=self.email_template_name,
            domain_override=settings.DOMAIN,
        )
        return super().form_valid(form)


# Restricted view template for managers
#@login_required
#@user_passes_test(manager_required, login_url='/login/')
#def add_warehouse_location(request):
    
# return render(request, 'url.html', {})

@login_required
@user_passes_test(manager_required)
def account_management(request, tenant_url=None):
    """View for managers to manage user accounts and pending registrations"""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    # Get all users for this tenant
    active_users = User.objects.all().exclude(id=request.user.id)
    
    # Get all pending registrations for this tenant
    pending_registrations = PendingRegistration.objects.filter(tenant_url=tenant_url).order_by('created_at')
    
    context = {
        "active_users": active_users,
        "pending_registrations": pending_registrations,
        "tenant_url": tenant_url,
    }
    
    return render(request, "userauth/account_management.html", context)

@login_required
@user_passes_test(manager_required)
def approve_registration(request, reg_id, tenant_url=None):
    """Approve a pending registration"""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        try:
            # Find the pending registration
            pending_reg = PendingRegistration.objects.get(id=reg_id)
            
            # Create a new user with the stored info
            user = User.objects.create(
                username=pending_reg.username,
                email=pending_reg.email,
                password=pending_reg.password  # Already hashed
            )
            
            # Set the user type to employee by default
            UserProfile.objects.create(user=user, user_type='employee')
            
            # Delete the pending registration
            pending_reg.delete()
            
            messages.success(request, f"Registration for {user.username} approved successfully.")
            
            # Redirect back to account management page
            return redirect(f'/{tenant_url}/userauth/account_management/')
            
        except PendingRegistration.DoesNotExist:
            messages.error(request, "Registration request not found.")
            return redirect(f'/{tenant_url}/userauth/account_management/')
    
    # If not POST, redirect to account management
    return redirect(f'/{tenant_url}/userauth/account_management/')

@login_required
@user_passes_test(manager_required)
def reject_registration(request, reg_id, tenant_url=None):
    """Reject a pending registration"""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        try:
            # Find the pending registration
            pending_reg = PendingRegistration.objects.get(id=reg_id)
            
            # Store username for success message
            username = pending_reg.username
            
            # Delete the pending registration
            pending_reg.delete()
            
            messages.success(request, f"Registration for {username} was rejected and deleted.")
            
            # Redirect back to account management page
            return redirect(f'/{tenant_url}/userauth/account_management/')
            
        except PendingRegistration.DoesNotExist:
            messages.error(request, "Registration request not found.")
            return redirect(f'/{tenant_url}/userauth/account_management/')
    
    # If not POST, redirect to account management
    return redirect(f'/{tenant_url}/userauth/account_management/')

@login_required
@user_passes_test(manager_required)
def update_user_type(request, user_id, tenant_url=None):
    """Update a user's type (employee/manager)"""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        try:
            user_type = request.POST.get('user_type')
            
            if user_type not in ['employee', 'manager']:
                messages.error(request, "Invalid user type specified.")
                return redirect(f'/{tenant_url}/userauth/account_management/')
            
            # Get the user to update
            user = User.objects.get(id=user_id)
            
            # Get or create their profile and update the user type
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.user_type = user_type
            profile.save()
            
            messages.success(request, f"User {user.username} updated to {user_type} successfully.")
            
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    
    # Redirect back to account management page
    return redirect(f'/{tenant_url}/userauth/account_management/')

@login_required
@user_passes_test(manager_required)
def delete_user(request, user_id, tenant_url=None):
    """Delete a user account"""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        try:
            # Find the user to delete
            user = User.objects.get(id=user_id)
            
            # Prevent deleting yourself
            if user.id == request.user.id:
                messages.error(request, "You cannot delete your own account.")
                return redirect(f'/{tenant_url}/userauth/account_management/')
            
            # Store username for success message
            username = user.username
            
            # Delete the user
            user.delete()
            
            messages.success(request, f"User {username} was deleted successfully.")
            
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    
    # Redirect back to account management page
    return redirect(f'/{tenant_url}/userauth/account_management/')

@login_required
@user_passes_test(manager_required)
def add_user(request, tenant_url=None):
    """Add a new user directly (manager only)"""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'employee')
        
        # Validate required fields
        if not all([username, email, password]):
            messages.error(request, "All fields are required.")
            return redirect(f'/{tenant_url}/userauth/account_management/')
        
        # Check for existing users
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect(f'/{tenant_url}/userauth/account_management/')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect(f'/{tenant_url}/userauth/account_management/')
        
        # Create the new user
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, user_type=user_type)
        
        messages.success(request, f"User {username} created successfully as {user_type}.")
        
    # Redirect back to account management page
    return redirect(f'/{tenant_url}/userauth/account_management/')


