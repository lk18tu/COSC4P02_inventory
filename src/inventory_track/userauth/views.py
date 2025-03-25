# userauth/views.py
import pytz
import datetime
import logging
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from .models import UserProfile
from notifications.models import Notification  # Import Notification from the notifications app
from inventory_analysis.views import generate_inventory_pie_chart
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)

# check if user is a manager
def manager_required(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.is_manager()

def register(request, company_path=None):
    """
    Register a new user within a tenant's context
    """
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validate data
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'userauth/register.html', {'company_path': company_path})
            
        # Create user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Account created successfully. You can now login.')
            return redirect(f'/{company_path}/userauth/login/')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    context = {
        'company_path': company_path,
        'company_name': request.tenant.name if hasattr(request, 'tenant') and request.tenant else '',
    }
    return render(request, 'userauth/register.html', context)

def user_login(request):
    """
    Handle user login within a tenant's context
    """
    # Get company_path from request object (set by middleware)
    company_path = getattr(request, 'company_path', None)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Redirect to the tenant's dashboard
            return redirect(f'/{company_path}/userauth/dashboard/')
        else:
            messages.error(request, 'Invalid username or password')
    
    context = {
        'company_path': company_path,
        'company_name': request.tenant.name if hasattr(request, 'tenant') and request.tenant else '',
    }
    return render(request, 'userauth/login.html', context)

@login_required
def user_logout(request):
    """
    Handle user logout within a tenant's context
    """
    # Get company_path from request object (set by middleware)
    company_path = getattr(request, 'company_path', None)
    
    logout(request)
    return redirect(f'/{company_path}/userauth/login/')

@login_required
def dashboard(request):
    """
    User dashboard
    """
    company_path = getattr(request, 'company_path', None)
    eastern = pytz.timezone('US/Eastern')
    current_time = datetime.datetime.now(eastern)
    formatted_date_time = current_time.strftime("%B %d, %Y, %I:%M %p EST")

    # Ensure user profile exists
    UserProfile.objects.get_or_create(user=request.user)
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count() or 0

    # Generate the pie chart (Base64-encoded image string)
    inventory_pie_chart = generate_inventory_pie_chart()

    context = {
        "unread_notifications": unread_notifications,
        "current_time": formatted_date_time,
        "is_manager": request.user.profile.is_manager(),
        "inventory_pie_chart": inventory_pie_chart,
        # If you also use "inventory_tables" for your dropdown, include it here
        # "inventory_tables": InvTable_Metadata.objects.filter(table_type="inventory"),
        'company_path': company_path,
        'company_name': request.tenant.name if hasattr(request, 'tenant') and request.tenant else '',
    }
    return render(request, "userauth/dashboard.html", context)

class ResetPasswordView(PasswordResetView):
    template_name = 'userauth/password_reset.html'
    email_template_name = 'userauth/password_reset_email.html'
    success_url = reverse_lazy('userauth:password_reset_done')

# Restricted view template for managers
#@login_required
#@user_passes_test(manager_required, login_url='/login/')
#def add_warehouse_location(request):
    
# return render(request, 'url.html', {})

def user_register(request, company_path=None):
    """
    Register a new user within a tenant's context
    """
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validate data
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'userauth/register.html', {'company_path': company_path})
            
        # Create user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, 'Account created successfully. You can now login.')
            return redirect(f'/{company_path}/userauth/login/')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    context = {
        'company_path': company_path,
        'company_name': request.tenant.name if hasattr(request, 'tenant') and request.tenant else '',
    }
    return render(request, 'userauth/register.html', context)


