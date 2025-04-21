from django.shortcuts import render


from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.contrib import messages
from django.forms import modelformset_factory

from .models import Supplier, SupplyOrder, SupplyOrderItem
from .forms import SupplyOrderForm, SupplyOrderItemForm


# ----------------------------------
# SUPPLIER VIEWS
# ----------------------------------
def supplier_list(request, tenant_url):
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'suppliers/supplier_list.html', {
         'suppliers':   suppliers,
         'tenant_url':  tenant_url,    
    })

def supplier_create(request, tenant_url):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone_number')
        address = request.POST.get('address')

        # Create supplier
        supplier = Supplier(
            name=name,
            email=email,
            phone_number=phone,
            address=address
        )
        supplier.save()
        messages.success(request, f"Supplier '{supplier.name}' created successfully!")
        return redirect('suppliers:supplier_list', tenant_url=tenant_url)

    return render(request, 'suppliers/supplier_create.html', {
         'tenant_url':  tenant_url,    
    })

def supplier_edit(request, tenant_url, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.email = request.POST.get('email')
        supplier.phone_number = request.POST.get('phone_number')
        supplier.address = request.POST.get('address')
        supplier.save()
        messages.success(request, f"Supplier '{supplier.name}' updated!")
        return redirect('suppliers:supplier_list', tenant_url=tenant_url)

    return render(request, 'suppliers/supplier_edit.html', {
         'supplier':   supplier,
         'tenant_url':  tenant_url,    
    })


# ----------------------------------
# SUPPLY ORDER VIEWS
# ----------------------------------
def order_list(request, tenant_url):
    orders = SupplyOrder.objects.select_related('supplier').order_by('-created_at')
    return render(request, 'suppliers/order_list.html', {
         'orders':   orders,
         'tenant_url':  tenant_url,    
    })


def order_create(request, tenant_url):
    ItemFormSet = modelformset_factory(SupplyOrderItem, form=SupplyOrderItemForm, extra=1)

    if request.method == 'POST':
        order_form = SupplyOrderForm(request.POST)
        formset    = ItemFormSet(request.POST, queryset=SupplyOrderItem.objects.none())

        if order_form.is_valid() and formset.is_valid():
            
            order = order_form.save(commit=False)
            order.location_name          = request.tenant.name
            order.destination_percentage = 0
            order.save()

            for item_form in formset:
                line = item_form.save(commit=False)
                line.supply_order = order
                line.save()

            messages.success(
                request,
                f"Supply‑order {order.tracking_number} created successfully!"
            )
            return redirect(
                reverse('suppliers:order_detail',
                        kwargs={'tenant_url': tenant_url, 'pk': order.pk})
            )
    else:
        order_form = SupplyOrderForm(initial={
            'location_name': request.tenant.name,
            'destination_percentage': 0
        })
        formset    = ItemFormSet(queryset=SupplyOrderItem.objects.none())

    return render(request, 'suppliers/order_create.html', {
        'order_form': order_form,
        'formset':    formset,
        'tenant_url':  tenant_url, 
    })


def order_detail(request, tenant_url, pk):
    order = get_object_or_404(SupplyOrder, pk=pk)
    return render(request, 'suppliers/order_detail.html', {
        'order': order,
        'tenant_url':  tenant_url, 
    })

@require_POST
def order_receive(request, tenant_url, pk):
    order = get_object_or_404(SupplyOrder, pk=pk)
    order.receive() 
    messages.success(
      request,
      f"Order {order.tracking_number} marked RECEIVED and inventory rows created."
    )
    return redirect(
      'suppliers:order_detail',
      tenant_url=tenant_url,
      pk=pk
    )