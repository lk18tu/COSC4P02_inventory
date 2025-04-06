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
from tenant_manager.views import tenant_landing
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('landing_page'), name='root'),
    path('tenant_manager/', include('tenant_manager.urls')),
    
    # Tenant-specific URLs
    path('<str:tenant_url>/', tenant_landing, name='tenant_landing'),
    path('<str:tenant_url>/userauth/', include('userauth.urls')),
    path('<str:tenant_url>/messaging/', include('messaging.urls')),
    path('<str:tenant_url>/updateStock/', include('updateStock.urls', namespace='updateStock')),
    path('<str:tenant_url>/manager/', include('manager.urls', namespace='manager')),
    path('<str:tenant_url>/notifications/', include('notifications.urls')),
    path('<str:tenant_url>/invManage/', include('inventoryApp.urls', namespace='inventoryApp')),
    path('<str:tenant_url>/inventory_analysis/', include('inventory_analysis.urls', namespace='inventory_analysis')),
    path('<str:tenant_url>/history/', include(('history.urls', 'history'), namespace='history')),
    path('<str:tenant_url>/suppliers/', include('suppliers.urls', namespace='suppliers')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)