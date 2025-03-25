from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import Product

# test to allow only managers (for example, staff users).
def is_manager(user):
    return user.is_staff

@user_passes_test(is_manager)
def view_stock(request):
    products = Product.objects.all()
    return render(request, 'manager/stock_view.html', {'products': products})
