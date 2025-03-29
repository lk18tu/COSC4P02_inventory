from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from .forms import TenantUserCreationForm, TenantCreationForm
from .models import Tenant
from django.contrib.auth.models import User
import re

def landing_page(request):
    return render(request, 'tenant_manager/landing.html')

def register_tenant(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                # Log the user in after registration
                login(request, user)
                messages.success(request, f'Account created for {username}. Welcome to your dashboard!')
                return redirect('tenant_dashboard')
        else:
            messages.error(request, 'Passwords do not match')
    
    return render(request, 'tenant_manager/register.html')

def tenant_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('tenant_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'tenant_manager/login.html')

def tenant_logout(request):
    logout(request)
    return redirect('landing_page')

@login_required
def tenant_dashboard(request):
    # Get all tenants owned by the current user
    tenants = Tenant.objects.filter(owner=request.user)
    return render(request, 'tenant_manager/dashboard.html', {'tenants': tenants})

@login_required
def add_tenant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        
        # Validate the name
        if not name:
            messages.error(request, 'Company name is required.')
            return redirect('tenant_dashboard')
        
        # Generate a URL-friendly version of the name
        domain_url = name.lower().replace(' ', '-')
        
        # Generate a database schema name
        schema_name = f"tenant_{domain_url.replace('-', '_')}"
        
        # Create the tenant
        try:
            tenant = Tenant.objects.create(
                name=name,
                domain_url=domain_url,
                schema_name=schema_name,
                owner=request.user,
            )
            
            # Create the database for this tenant
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{schema_name}`")
            except Exception as e:
                print(f"Error creating database: {str(e)}")
                # If we can't create the database, we should still keep the tenant
            
            messages.success(request, f'Company "{name}" created successfully!')
            return redirect('tenant_dashboard')  # Redirect back to dashboard
        except Exception as e:
            messages.error(request, f'Error creating company: {str(e)}')
            return redirect('tenant_dashboard')  # Redirect back to dashboard on error too
    
    # If this is a GET request, redirect to dashboard
    return redirect('tenant_dashboard')

@login_required
def delete_tenant(request, tenant_id):
    try:
        tenant = Tenant.objects.get(id=tenant_id, owner=request.user)
        
        if request.method == 'POST':
            schema_name = tenant.schema_name
            
            # Store the tenant name for the success message
            tenant_name = tenant.name
            
            # Delete the tenant first
            tenant.delete()
            
            # Check if schema_name exists and is not empty before trying to drop database
            if schema_name and schema_name.strip():
                try:
                    # Drop the tenant's database schema with proper error handling
                    with connection.cursor() as cursor:
                        cursor.execute(f"DROP DATABASE IF EXISTS `{schema_name}`")
                except Exception as e:
                    # Log the error but don't block the tenant deletion
                    print(f"Error dropping database schema: {str(e)}")
                    
            messages.success(request, f'Company {tenant_name} has been deleted.')
            return redirect('tenant_dashboard')
            
        return render(request, 'tenant_manager/delete_tenant.html', {'tenant': tenant})
        
    except Tenant.DoesNotExist:
        messages.error(request, 'Company not found or you do not have permission to delete it.')
        return redirect('tenant_dashboard')

def tenant_landing(request, tenant_url):
    try:
        tenant = Tenant.objects.get(domain_url=tenant_url, is_active=True)
        return render(request, 'tenant_landing.html', {'tenant': tenant, 'tenant_url': tenant_url})
    except Tenant.DoesNotExist:
        return redirect('landing_page')
