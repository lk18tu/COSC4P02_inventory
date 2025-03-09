from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('userauth/', include('userauth.urls')),  # Include userauth app URLs
    path('messaging/', include(('messaging.urls', 'messaging'), namespace='messaging')),  # Add Messaging app
    path('updateStock/', include(('updateStock.urls', 'updateStock'), namespace='updateStock')),  # URLs for stock update
    path('manager/', include(('manager.urls', 'manager'), namespace='manager')),  # Manager app
    path('notifications/', include('notifications.urls')),  # Notifications app
    path('invManage/', include('inventoryApp.urls')),  # Inventory Management app
    path("", lambda request: redirect("userauth/login/")),  # Redirect root to userauth login
]
