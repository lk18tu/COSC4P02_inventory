from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import connections, connection
from .models import Tenant
import random
import string
import mysql.connector
from django.conf import settings
from .forms import TenantForm
from .connection import set_current_tenant, create_tenant_database
from .db_utils import initialize_tenant_database

def random_string(length=8):
    """Generate a random string of letters and digits"""
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

def landing_page(request):
    """Landing page for the application"""
    return render(request, 'tenant_manager/landing_page.html')

def tenant_register(request):
    """Register a new tenant/company owner"""
    if request.method == 'POST':
        try:
            company_name = request.POST['company_name']
            company_path = request.POST['company_path']
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            
            # Check if company path already exists
            if Tenant.objects.filter(company_path=company_path).exists():
                messages.error(request, 'Company URL path already taken. Please choose another.')
                return render(request, 'tenant_manager/register.html')
            
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            # Generate database name
            db_name = f"tenant_{company_path}_{random_string(8)}"
            
            # Create the tenant database
            create_tenant_database(db_name)
            
            # Create tenant record
            tenant = Tenant.objects.create(
                name=company_name,
                company_path=company_path,
                owner=user,
                db_name=db_name
            )
            
            # Initialize tenant database
            initialize_tenant_database(db_name)
            
            messages.success(request, 'Registration successful! You can now login')
            return redirect('tenant_manager:tenant_login')
            
        except Exception as e:
            messages.error(request, f'Error creating tenant: {str(e)}')
            
    return render(request, 'tenant_manager/register.html')

def tenant_login(request):
    """Login for tenant owners"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('tenant_manager:tenant_dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'tenant_manager/login.html')

@login_required
def tenant_dashboard(request):
    """Dashboard for tenant management"""
    # Get tenants owned by the current user
    tenants = Tenant.objects.filter(owner=request.user)
    return render(request, 'tenant_manager/dashboard.html', {'tenants': tenants})

@login_required
def create_tenant(request):
    """Create a new tenant/company"""
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            # Get form data
            company_name = form.cleaned_data['name']
            company_path = form.cleaned_data['company_path']
            
            # Generate database name
            db_name = f"tenant_{company_path}_{random_string(8)}"
            
            try:
                # Create the tenant database
                create_tenant_database(db_name)
                
                # Create tenant record but don't save yet
                tenant = form.save(commit=False)
                tenant.owner = request.user
                tenant.db_name = db_name
                tenant.save()
                
                # Initialize tenant database
                initialize_tenant_database(db_name)
                
                messages.success(request, f'Company "{company_name}" created successfully')
                return redirect('tenant_manager:tenant_dashboard')
                
            except Exception as e:
                messages.error(request, f'Error creating tenant: {str(e)}')
    else:
        form = TenantForm()
        
    return render(request, 'tenant_manager/create_tenant.html', {'form': form})
