"""
URL configuration for inventory_track project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

# Create a tenant admin site
tenant_admin_site = admin.AdminSite(name='tenant_admin')

# Register models with the tenant admin site
from django.contrib.auth.models import User, Group
from tenant_manager.models import Tenant
tenant_admin_site.register(User)
tenant_admin_site.register(Group)
tenant_admin_site.register(Tenant)

urlpatterns = [
    # Global admin site
    path('admin/', admin.site.urls),
    
    # Tenant manager URLs (for managing tenants)
    path('', include('tenant_manager.urls', namespace='tenant_manager')),
    
    # Tenant-specific paths
    path('<str:company_path>/admin/', tenant_admin_site.urls),
    path('<str:company_path>/userauth/', include('userauth.urls')),
    path('<str:company_path>/messaging/', include('messaging.urls')),
    path('<str:company_path>/updateStock/', include('updateStock.urls', namespace='updateStock')),
    path('<str:company_path>/manager/', include('manager.urls', namespace='manager')),
    path('<str:company_path>/notifications/', include('notifications.urls')),
    path('<str:company_path>/invManage/', include('inventoryApp.urls', namespace='inventoryApp')),
    path('<str:company_path>/inventory_analysis/', include('inventory_analysis.urls', namespace='inventory_analysis')),
    path('<str:company_path>/history/', include(('history.urls', 'history'), namespace='history')),
    path('<str:company_path>/suppliers/', include('suppliers.urls', namespace='suppliers')),
    
    # Default redirect for company paths to their login page
    path('<str:company_path>/', lambda request, company_path: redirect(f"/{company_path}/userauth/login/")),
]
