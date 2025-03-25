#from django.shortcuts import render, redirect
#from django.contrib.auth import login, authenticate, logout
#from django.contrib.auth.decorators import login_required
#from django.contrib.auth.forms import AuthenticationForm
#from .forms import RegistrationForm

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        
        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'user already exists')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'email already exists')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                messages.success(request, 'registration successful')
                return redirect('login')
        else:
            messages.error(request, 'passwords do not match')
    return render(request, 'userauth/register.html')


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'username or password does not match')
    return render(request, 'userauth/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    return render(request, 'userauth/dashboard.html')

