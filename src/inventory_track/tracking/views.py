from django.shortcuts import render, Http404
from django.db import connection
from inventoryApp.models import InvTable_Metadata
import qrcode
from io import BytesIO
from django.http import HttpResponse

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
                item_data = dict(zip(columns, item))  # keep your current 'item'
                item_data['destination_percent_display'] = float(item_data.get('destination_percentage', 0)) * 100


                # Prepare to fetch class info
                class_table = table_name.replace("_items", "_classes")
                class_id = item_data.get("class_id")

                # Query the class table
                cursor.execute(f"SELECT title, product_number FROM `{class_table}` WHERE id = %s", [class_id])
                class_row = cursor.fetchone()
                item_class = {"title": None, "product_number": None}
                if class_row:
                    item_class["title"] = class_row[0]
                    item_class["product_number"] = class_row[1]

                return render(request, 'tracking/item_tracking_detail.html', {
                    'item': item_data,
                    'item_class': item_class,  # new dict
                    'table_name': table_name,
                    'tenant_url': tenant_url,
                })

    raise Http404("Item not found")




def generate_qr(request, tenant_url=None):
    data = request.GET.get("data", "")
    if not data:
        return HttpResponse("Missing data", status=400)

    qr = qrcode.make(data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type="image/png")

