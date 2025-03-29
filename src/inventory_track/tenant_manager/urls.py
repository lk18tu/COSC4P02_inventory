from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('register/', views.register_tenant, name='register_tenant'),
    path('login/', views.tenant_login, name='tenant_login'),
    path('logout/', views.tenant_logout, name='tenant_logout'),
    path('dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('add-tenant/', views.add_tenant, name='add_tenant'),
    path('delete-tenant/<int:tenant_id>/', views.delete_tenant, name='delete_tenant'),
]
