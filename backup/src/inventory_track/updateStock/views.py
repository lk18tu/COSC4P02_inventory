from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product
from .forms import ProductStockUpdateForm

@login_required
def product_list(request):
    """Display a list of all products with current stock levels."""
    products = Product.objects.all()
    return render(request, 'updateStock/product_list.html', {'products': products})


@login_required
def update_stock(request, pk):
    """Allow warehouse staff to update the stock of a specific product."""
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductStockUpdateForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('updateStock:product_list')
    else:
        form = ProductStockUpdateForm(instance=product)
    return render(request, 'updateStock/update_stock.html', {'form': form, 'product': product})

