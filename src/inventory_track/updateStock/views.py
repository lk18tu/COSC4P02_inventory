from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from inventoryApp.models import InvItem  # Use the inventory management model
from .forms import ProductStockUpdateForm

@login_required
def product_list(request):
    """Display a list of all products from the inventory management table."""
    products = InvItem.objects.all()
    return render(request, 'updateStock/product_list.html', {'products': products})

@login_required
def update_stock(request, pk):
    """Allow warehouse staff to update the stock of a specific product."""
    # Use InvItem model here so we update the inventory management table
    product = get_object_or_404(InvItem, pk=pk)
    if request.method == 'POST':
        form = ProductStockUpdateForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('updateStock:product_list')
    else:
        form = ProductStockUpdateForm(instance=product)
    return render(request, 'updateStock/update_stock.html', {'form': form, 'product': product})
