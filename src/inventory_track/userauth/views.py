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

logger = logging.getLogger(__name__)

# check if user is a manager
def manager_required(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.is_manager()

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'User already exists')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                # UserProfile with default 'employee' type
                UserProfile.objects.create(user=user)
                user.save()
                messages.success(request, 'Registration successful')
                return redirect('login')
        else:
            messages.error(request, 'Passwords do not match')
    return render(request, 'userauth/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # profile exists (for existing users)
            UserProfile.objects.get_or_create(user=user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username or password does not match')
    return render(request, 'userauth/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
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
    }
    return render(request, "userauth/dashboard.html", context)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'userauth/password_reset.html'
    email_template_name = 'userauth/password_reset_email.html'
    subject_template_name = 'userauth/password_reset_subject.txt'
    success_message = "We've emailed you instructions for setting your password, if an account exists with the email you entered."
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


