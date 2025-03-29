from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User

class RegistrationForm(UserCreationForm):

	email = forms.EmailField(required=True)

	class Meta:

		model=User
		fields = ['username','email','password1','password2']

class LoginForm(AuthenticationForm):
	
	username = forms.CharField(label="Username", max_length=60)
	password = forms.CharField(label="Password", widget=forms.PasswordInput)

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Email", max_length=254)

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label="New password", widget=forms.PasswordInput)
    new_password2 = forms.CharField(label="Confirm new password", widget=forms.PasswordInput)

