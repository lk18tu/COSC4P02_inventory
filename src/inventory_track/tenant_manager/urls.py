from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'tenant_manager'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('register/', views.tenant_register, name='tenant_register'),
    path('login/', views.tenant_login, name='tenant_login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('create/', views.create_tenant, name='create_tenant'),
] 