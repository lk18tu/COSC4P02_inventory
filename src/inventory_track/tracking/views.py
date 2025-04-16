from django.shortcuts import render, Http404
from django.db import connection
from inventoryApp.models import InvTable_Metadata

def tracking_home(request, tenant_url=None):
    tracking_number = request.GET.get('tracking_number')
    result = None
    searched = False

    if tracking_number:
        searched = True
        tables = InvTable_Metadata.objects.filter(table_type="inventory_individual_items")
        for table in tables:
            with connection.cursor() as cursor:
                try:
                    cursor.execute(f"SELECT * FROM `{table.table_name}` WHERE tracking_number = %s", [tracking_number])
                    row = cursor.fetchone()
                    if row:
                        columns = [col[0] for col in cursor.description]
                        result = dict(zip(columns, row))
                        break
                except Exception as e:
                    print(f"Error searching in table {table.table_name}: {str(e)}")

    return render(request, 'tracking/tracking_home.html', {
        'result': result,
        'searched': searched,
        'tenant_url': tenant_url
    })


def tracked_item_detail(request, tracking_number, tenant_url=None):
    with connection.cursor() as cursor:
        cursor.execute("SELECT table_name FROM inventoryApp_invtable_metadata WHERE table_type = 'inventory_individual_items'")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM `{table_name}` WHERE tracking_number = %s", [tracking_number])
            item = cursor.fetchone()
            if item:
                columns = [col[0] for col in cursor.description]
                item_data = dict(zip(columns, item))
                item_data['destination_percent_display'] = round(item_data['destination_percentage'] * 100, 2)

                return render(request, 'tracking/item_tracking_detail.html', {'item': item_data, 'table_name': table_name})

    raise Http404("Item not found")
