from django import forms
from .models import SupplyOrder, SupplyOrderItem, Supplier
from inventoryApp.models import InvItem

class SupplyOrderForm(forms.ModelForm):
    class Meta:
        model = SupplyOrder
        fields = ['supplier', 'location_name']

class SupplyOrderItemForm(forms.ModelForm):
    inventory_item = forms.ModelChoiceField(queryset=InvItem.objects.all())

    class Meta:
        model = SupplyOrderItem
        fields = ['inventory_item', 'quantity']
