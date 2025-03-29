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
from django.http import JsonResponse

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
            else:
                # Use password1 from the modal form
                user = User.objects.create_user(username=username, email=email, password=password1)
                
                # Check if this is the first user for this tenant
                is_first_user = User.objects.count() == 1
                
                # Create UserProfile - make first user a manager
                if is_first_user:
                    UserProfile.objects.create(user=user, user_type='manager')
                else:
                    UserProfile.objects.create(user=user, user_type='employee')
                
                # Log the user in automatically
                login(request, user)
                
                messages.success(request, 'Registration successful')
                
                if is_ajax:
                    return JsonResponse({
                        'status': 'success', 
                        'message': 'Registration successful',
                        'redirect_url': f'/{tenant_url}/userauth/dashboard/'
                    })
                    
                # Redirect directly to dashboard instead of login page
                return redirect(f'/{tenant_url}/userauth/dashboard/')
    
    # For GET requests, this should never be called if the template is deprecated
    return redirect(f'/{tenant_url}/')

def user_login(request, tenant_url=None):
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # profile exists (for existing users)
            UserProfile.objects.get_or_create(user=user)
            return redirect(f'/{tenant_url}/userauth/dashboard/')
        else:
            messages.error(request, 'Username or password does not match')
    return render(request, 'userauth/login.html', {'tenant_url': tenant_url})

def user_logout(request, tenant_url=None):
    """Logs out the user and redirects to the tenant landing page."""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    logout(request)
    # Redirect to the tenant landing page instead of the login page
    return redirect(f'/{tenant_url}/')

@login_required
def dashboard(request, tenant_url=None):
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
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
        "tenant_url": tenant_url,
    }
    return render(request, "userauth/dashboard.html", context)


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


