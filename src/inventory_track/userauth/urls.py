from django.urls import path
from . import views
from django.contrib.auth.views import PasswordResetDoneView, PasswordResetCompleteView, PasswordResetConfirmView

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # Account management
    path('account_management/', views.account_management, name='account_management'),
    path('approve_registration/<int:reg_id>/', views.approve_registration, name='approve_registration'),
    path('reject_registration/<int:reg_id>/', views.reject_registration, name='reject_registration'),
    path('update_user_type/<int:user_id>/', views.update_user_type, name='update_user_type'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('add_user/', views.add_user, name='add_user'),
    # Password reset
    path('password_reset/', views.ResetPasswordView.as_view(), name='password_reset'),
    path('password_reset/done/', PasswordResetDoneView.as_view(template_name='userauth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='userauth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='userauth/password_reset_complete.html'), name='password_reset_complete'),
]
