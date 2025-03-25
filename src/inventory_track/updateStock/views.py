from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.db import connection
from django.contrib import messages
from django.http import Http404
from inventoryApp.models import InvTable_Metadata
from django.conf import settings

def product_list(request):
    """
    Display data from a selected inventory table.
    If no table is selected via GET, default to the first available inventory table.
    """
    # Get the selected table name from GET parameters
    table_name = request.GET.get('table')

    # Retrieve all available inventory tables (for the dropdown)
    inventory_tables = InvTable_Metadata.objects.filter(table_type="inventory").order_by('table_name')

    # Default to the first available table if none was selected
    if not table_name and inventory_tables.exists():
        table_name = inventory_tables.first().table_name

    table_data = {}
    if table_name:
        try:
            with connection.cursor() as cursor:
                # Fetch all data from the selected table
                cursor.execute(f"SELECT * FROM {table_name}")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                table_data = {
                    'table_name': table_name,
                    'columns': columns,
                    'rows': rows
                }
        except Exception as e:
            messages.error(request, f"Error fetching data for table {table_name}: {e}")

    return render(request, 'updateStock/product_list.html', {
        'table_data': table_data,
        'inventory_tables': inventory_tables,
        'MEDIA_URL': settings.MEDIA_URL
    })

def update_stock(request, table_name, item_id):
    """
    Update the quantity_stock field for a given item in the specified table.
    """
    if request.method == 'POST':
        new_quantity = request.POST.get('quantity')
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE {table_name} SET quantity_stock = %s WHERE id = %s",
                    [new_quantity, item_id]
                )
            messages.success(request, "Stock updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating stock: {e}")
        # Redirect to the correct URL (note the path is '/updateStock/products/')
        return redirect(f"/updateStock/products/?table={table_name}")
    else:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT quantity_stock FROM {table_name} WHERE id = %s",
                    [item_id]
                )
                row = cursor.fetchone()
                if row:
                    current_quantity = row[0]
                else:
                    raise Http404("Item not found.")
        except Exception as e:
            messages.error(request, f"Error fetching item data: {e}")
            return redirect(f"/updateStock/products/?table={table_name}")
        return render(request, 'updateStock/update_stock.html', {
            'table_name': table_name,
            'item_id': item_id,
            'current_quantity': current_quantity
        })
