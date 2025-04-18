from django import forms

class StockForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        label="Quantity"
    )
