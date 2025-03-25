from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from datetime import date

from .models import Supplier, SupplyOrder, SupplyOrderItem
from inventoryApp.models import InvItem

# ----------------------------------
# SUPPLIER VIEWS
# ----------------------------------
def supplier_list(request):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'suppliers/supplier_list.html', {'suppliers': suppliers})

def supplier_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_person = request.POST.get('contact_person')
        email = request.POST.get('email')
        phone = request.POST.get('phone_number')
        address = request.POST.get('address')

        # Create supplier
        supplier = Supplier(
            name=name,
            contact_person=contact_person,
            email=email,
            phone_number=phone,
            address=address
        )
        supplier.save()
        messages.success(request, f"Supplier '{supplier.name}' created successfully!")
        return redirect('suppliers:supplier_list')

    return render(request, 'suppliers/supplier_create.html')

def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.contact_person = request.POST.get('contact_person')
        supplier.email = request.POST.get('email')
        supplier.phone_number = request.POST.get('phone_number')
        supplier.address = request.POST.get('address')
        supplier.save()
        messages.success(request, f"Supplier '{supplier.name}' updated!")
        return redirect('suppliers:supplier_list')

    return render(request, 'suppliers/supplier_edit.html', {'supplier': supplier})


# ----------------------------------
# SUPPLY ORDER VIEWS
# ----------------------------------
def order_list(request):
    orders = SupplyOrder.objects.select_related('supplier').order_by('-order_date')
    return render(request, 'suppliers/order_list.html', {'orders': orders})

def order_create(request):
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        order_date = request.POST.get('order_date', str(date.today()))
        status = request.POST.get('status', 'PENDING')
        notes = request.POST.get('notes')

        supplier = get_object_or_404(Supplier, pk=supplier_id)

        supply_order = SupplyOrder(
            supplier=supplier,
            order_date=order_date,
            status=status,
            notes=notes
        )
        supply_order.save()

        # Optionally handle items in the same form or a separate view
        # ...

        messages.success(request, f"Supply order created for supplier '{supplier.name}'!")
        return redirect('suppliers:order_list')

    suppliers = Supplier.objects.all()
    return render(request, 'suppliers/order_create.html', {
        'suppliers': suppliers,
    })

def order_detail(request, pk):
    supply_order = get_object_or_404(SupplyOrder, pk=pk)
    order_items = supply_order.order_items.select_related('inventory_item')
    return render(request, 'suppliers/order_detail.html', {
        'supply_order': supply_order,
        'order_items': order_items
    })
