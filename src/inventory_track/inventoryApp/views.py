from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import InvItem, InvTable_Metadata
from history.models import InventoryHistory
from userauth.models import UserProfile
from django.db import connection, DatabaseError
from django.contrib import messages
from django.http import Http404
from django.conf import settings
import datetime
import csv, os
from tenant_manager.utils import tenant_context
from django.db import IntegrityError
from django.contrib import messages


#table_name = f"testuser_invtable"  # Adjust based on the current user

# Create your views here.
def home(request, tenant_url=None):
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''

    #get company name
    tenant = getattr(request, 'tenant', None)
    company_name = tenant.name if tenant else 'Unknown Company'
    

    # Get all inventory tables
    inventory_tables = InvTable_Metadata.objects.filter(table_type="inventory", company_name=company_name)
    
    # Get archived tables
    archived_tables = InvTable_Metadata.objects.filter(table_type="archived_inventory", company_name=company_name)
    
    # Determine which view to show (normal or archived)
    current_view = request.GET.get("view", "inventory")
    
    # Fetch data for each table
    table_data = []
    tables_to_display = inventory_tables if current_view == "inventory" else archived_tables
    
    print(f"Found {len(tables_to_display)} tables to display")
    
    for table in tables_to_display:
        try:
            with connection.cursor() as cursor:
                # Fetch all data from the selected table
                cursor.execute(f"SELECT * FROM {table.table_name}")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                print(f"Table {table.table_name} has {len(rows)} rows and columns: {columns}")
                table_data.append({
                    'table_name': table.table_name,
                    'table_friendly_name': table.table_friendly_name,
                    'columns': columns,
                    'rows': rows
                })
        except Exception as e:
            print(f"Error fetching data for table {table.table_name}: {e}")
    
    context = {
        "inventory_tables": inventory_tables,
        "archived_tables": archived_tables,
        "current_view": current_view,
        "tenant_url": tenant_url,
        "table_data": table_data,
    }
    
    return render(request, "inventoryApp/inventoryHome.html", context)

def add_custom_field(request):
    if request.method == "POST":
        field_name = request.POST.get("field_name")
        field_value = request.POST.get("field_value", "")

        if field_name:
            try:
                # Fetch an item to update (modify based on your logic)
                item = InvItem.objects.first()  # Get the first item for demo purposes

                if item:
                    # Update the JSON field dynamically
                    item.custom_fields[field_name] = field_value
                    item.save()
                    messages.success(request, f"Custom field '{field_name}' added successfully!")
                else:
                    messages.error(request, "No inventory items found.")

            except Exception as e:
                messages.error(request, f"Error: {e}")

        return redirect("InventoryApp:home")

    return render(request, "add_custom_field.html")



import os
from django.shortcuts import render, redirect
from django.conf import settings
from django.db import connection
from django.http import Http404

def add_item(request, table_name, tenant_url=None):
    form_data = {}  # Store the entered values

    if request.method == "POST":
        # Get form data
        form_data = {
            'product_number': request.POST.get('product_number'),
            'upc': request.POST.get('upc'),
            'title': request.POST.get('title'),
            'description': request.POST.get('description'),
            'reorder_level': request.POST.get('reorder_level'),
            'price': request.POST.get('price'),
            'purchase_price': request.POST.get('purchase_price'),
            'notes': request.POST.get('notes'),
        }
        image = request.FILES.get('image')

        # Validate required fields
        required_fields = ['product_number', 'title', 'reorder_level']
        missing_fields = [field for field in required_fields if not form_data[field]]
        
        if missing_fields:
            messages.error(request, f"Please fill in all required fields: {', '.join(missing_fields)}")
            return render(request, "inventoryApp/add_item.html", {
                "table_name": table_name,
                "friendly_name": get_friendly_table_name(table_name),
                "form_data": form_data
            })

        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                result = cursor.fetchone()

                if result:
                    # Save image
                    image_path = None
                    if image:
                        image_path = os.path.join('inventory_images', image.name)
                        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'wb+') as destination:
                            for chunk in image.chunks():
                                destination.write(chunk)
                    else:
                        image_path = 'images/default_placeholder.png'

                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} (
                            product_number, upc, title, description, 
                            quantity_stock, reorder_level, price, 
                            purchase_price, notes, image
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            form_data['product_number'], form_data['upc'], form_data['title'], form_data['description'],
                            0, form_data['reorder_level'], form_data['price'],
                            form_data['purchase_price'], form_data['notes'], image_path
                        ]
                    )

                    item_class_id = cursor.lastrowid

                    InventoryHistory.objects.create(
                        location=table_name,
                        user=request.user,
                        action="add",
                        details="Added item class: " + form_data['title'] + " " + str(form_data['product_number']),
                        item_class_number=item_class_id,
                    )

                    tenant = getattr(request, 'tenant', None)
                    tenant_url = tenant.domain_url if tenant else tenant_url or ''
                    return redirect(f"/{tenant_url}/invManage/")
                else:
                    raise Http404(f"Table '{table_name}' does not exist.")

        except IntegrityError as e:
            if "Duplicate entry" in str(e):
                messages.error(request, "That product number or UPC already exists.")
            else:
                messages.error(request, "A database error occurred.")
        except Exception as e:
            print(f"Error adding item to table {table_name}: {str(e)}")
            messages.error(request, "Unexpected error while adding the item.")

    return render(request, "inventoryApp/add_item.html", {
        "table_name": table_name,
        "friendly_name": get_friendly_table_name(table_name),
        "form_data": form_data
    })

from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .models import InvTable_Metadata  # Ensure this is imported
from .utils import log_inventory_action  # Assuming this is a custom function

def add_inventory(request, tenant_url=None):
    tenant = getattr(request, 'tenant', None)
    company_name = tenant.name if tenant else 'Unknown Company'
    
    if request.method == "POST":
        Friendly_new_table_name = request.POST.get("table_name")
        new_table_name = Friendly_new_table_name.replace(" ", "")

        # Basic validation
        if not new_table_name.isalnum():
            messages.error(request, "Error: Table name must be alphanumeric.")
            return render(request, "inventoryApp/add_inventory.html")

        new_table_name = company_name.replace(" ", "") + "_" + new_table_name

        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                print(f"Creating table {new_table_name} in database {current_db}")

                # Create class table
                cursor.execute(f"""
                    CREATE TABLE `{new_table_name}_classes` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_number VARCHAR(100) UNIQUE,
                        upc VARCHAR(255) UNIQUE,
                        title VARCHAR(255),
                        description VARCHAR(255),
                        quantity_stock INT,
                        reorder_level INT,
                        price DECIMAL(10, 2),
                        purchase_price DECIMAL(10, 2),
                        image VARCHAR(255),
                        notes VARCHAR(255)
                    )
                """)

                # Create item tracking table
                cursor.execute(f"""
                    CREATE TABLE `{new_table_name}_items` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        class_id INT,
                        tracking_number VARCHAR(100) UNIQUE,
                        status VARCHAR(20),
                        location VARCHAR(100),
                        destination_percentage DOUBLE(5,2),
                        date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (class_id) REFERENCES {new_table_name}_classes(id)
                    )
                """)

                # Metadata entries
                InvTable_Metadata.objects.create(
                    table_name=f"{new_table_name}_classes",
                    table_type="inventory",
                    table_friendly_name=Friendly_new_table_name,
                    company_name=company_name
                )
                InvTable_Metadata.objects.create(
                    table_name=f"{new_table_name}_items",
                    table_type="inventory_individual_items",
                    table_friendly_name=Friendly_new_table_name,
                    company_name=company_name
                )

                # Log history
                InventoryHistory.objects.create(
                    location=new_table_name,
                    user=request.user,
                    action="add",
                    details="Added Location: " + new_table_name,
                )

            tenant_url = tenant.domain_url if tenant else ''
            return redirect(f"/{tenant_url}/invManage/")

        except Exception as e:
            print(f"Error creating inventory table: {str(e)}")
            messages.error(request, f"Failed to create inventory table: {str(e)}")
            return render(request, "inventoryApp/add_inventory.html")

    return render(request, "inventoryApp/add_inventory.html")


def archive_table(request, table_name, tenant_url=None):
    if request.method == 'POST':  # Only allow POST request for safety
        try:
            # Get the table entry from metadata
            table_metadata = get_object_or_404(InvTable_Metadata, table_name=table_name)

            # Update table_type to 'archived_inventory'
            table_metadata.table_type = 'archived_inventory'
            table_metadata.save()

            print(f"Table '{table_name}' archived successfully.")
            # log change
            InventoryHistory.objects.create(
                location = table_name,
                user = request.user,
                action = "archive",
                details = "Archived Location: " + table_name,
            )
            
            # Get tenant URL for redirect
            tenant = getattr(request, 'tenant', None)
            tenant_url = tenant.domain_url if tenant else tenant_url or ''
            return redirect(f"/{tenant_url}/invManage/")
        except Exception as e:
            print(f"Error archiving table '{table_name}': {e}")
            tenant = getattr(request, 'tenant', None)
            tenant_url = tenant.domain_url if tenant else tenant_url or ''
            return redirect(f"/{tenant_url}/invManage/")

def unarchive_table(request, table_name, tenant_url=None):
    if request.method == 'POST':  # Only allow POST request for safety
        try:
            # Get the table entry from metadata
            table_metadata = get_object_or_404(InvTable_Metadata, table_name=table_name)

            # Update table_type to 'archived_inventory'
            table_metadata.table_type = 'inventory'
            table_metadata.save()

            print(f"Table '{table_name}' unarchived successfully.")

            InventoryHistory.objects.create(
                location = table_name,
                user = request.user,
                action = "unarchive",
                details = "Unarchived Location: " + table_name,
            )
            
            # Get tenant URL for redirect
            tenant = getattr(request, 'tenant', None)
            tenant_url = tenant.domain_url if tenant else tenant_url or ''
            return redirect(f"/{tenant_url}/invManage/")
        except Exception as e:
            print(f"Error unarchiving table '{table_name}': {e}")
            tenant = getattr(request, 'tenant', None)
            tenant_url = tenant.domain_url if tenant else tenant_url or ''
            return redirect(f"/{tenant_url}/invManage/")



def delete_item(request, table_name, item_id, tenant_url=None):
    # First check if the table exists
    with connection.cursor() as cursor:
        cursor.execute(f"SHOW TABLES LIKE %s", [table_name])
        if not cursor.fetchone():
            raise Http404(f"Table '{table_name}' does not exist.")

        # Check if the item exists
        cursor.execute(f"SELECT title, product_number FROM {table_name} WHERE id = %s", [item_id])
        row = cursor.fetchone()
        if not row:
            raise Http404(f"Item with ID {item_id} not found.")
        title, product_number = row

    try:
        # Delete the item
        with connection.cursor() as cursor:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", [item_id])

        # Log the deletion
        InventoryHistory.objects.create(
            location=table_name,
            user=request.user,
            action="delete",
            details=f"Deleted item class: {title} {product_number}",
            item_class_number=item_id,
        )

        # Redirect
        tenant = getattr(request, 'tenant', None)
        tenant_url = tenant.domain_url if tenant else tenant_url or ''
        return redirect(f"/{tenant_url}/invManage/")
    except Exception as e:
        print(f"Error deleting item: {str(e)}")
        tenant = getattr(request, 'tenant', None)
        tenant_url = tenant.domain_url if tenant else tenant_url or ''
        return redirect(f"/{tenant_url}/invManage/")



def edit_item(request, table_name, item_id, tenant_url=None):
    # Fetch the item details to pre-fill the form
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT * FROM {table_name} WHERE id = %s
            """, [item_id])
            item = cursor.fetchone()
            if not item:
                raise Http404(f"Item with ID {item_id} not found in table {table_name}.")
            
            # Column names based on your DB structure
            item_columns = ['id', 'product_number', 'upc', 'title', 'description', 'quantity_stock', 
                           'reorder_level', 'price', 'purchase_price', 'image', 'notes']
            
            # Map SQL result to dictionary
            item_data = {col: item[i] for i, col in enumerate(item_columns) if i < len(item)}

    except Http404:
        raise
    except Exception as e:
        return HttpResponse(f"<h1>Error fetching item:</h1><p>{str(e)}</p>", status=500)
    
    if request.method == 'POST':
        # Get data from the form
        title = request.POST['title']
        description = request.POST['description']
        reorder_level = request.POST['reorder_level']
        price = request.POST['price']
        purchase_price = request.POST['purchase_price']
        notes = request.POST['notes']

        # Handle file upload (only update if a new file is provided)
        image = request.FILES.get('image', None)
        image_filename = item_data.get('image')  # Keep the existing image by default

        if image:
            # Save new image
            image_dir = os.path.join(settings.MEDIA_ROOT, 'inventory_images')
            os.makedirs(image_dir, exist_ok=True)  # Ensure directory exists
            
            image_filename = f"{table_name}_{item_id}_{image.name}"
            image_path = os.path.join(image_dir, image_filename)

            with open(image_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)

            # Store the relative path to the database
            image_filename = f"inventory_images/{image_filename}"

        try:
            # Update item in the database
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET title = %s, description = %s, reorder_level = %s, 
                        price = %s, purchase_price = %s, notes = %s, image = %s
                    WHERE id = %s
                """, [title, description, reorder_level, price, purchase_price, notes, image_filename, item_id])

            #log history
            InventoryHistory.objects.create(
                location=table_name,
                user=request.user,
                action="update",
                details="Updated Class: " + title,
                item_class_number=item_id
            )

            # Redirect after saving
            tenant = getattr(request, 'tenant', None)
            tenant_url = tenant.domain_url if tenant else tenant_url or ''
            return redirect(f"/{tenant_url}/invManage/")

        except Exception as e:
            return HttpResponse(f"<h1>Error updating item:</h1><p>{str(e)}</p>", status=500)

    return render(request, 'inventoryApp/edit_item.html', {'item': item_data, 'table_name': table_name, 'friendly_name': get_friendly_table_name(table_name)})






def upload_csv(request, table_name, tenant_url=None):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        mode = request.POST.get('upload_mode')

        if not csv_file or not csv_file.name.endswith('.csv'):
            return render(request, 'inventoryApp/csv_upload.html', {
                'table_name': table_name,
                'error_message': "Invalid file format. Please upload a .csv file."
            })

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        headers = next(reader)

        expected_headers = ["Product Number", "UPC", "Title", "Description",
                            "Reorder Level", "Price", "Purchase Price", "Notes"]

        if headers != expected_headers:
            return render(request, 'inventoryApp/csv_upload.html', {
                'table_name': table_name,
                'error_message': "Invalid CSV format. Ensure headers match the template exactly."
            })

        with connection.cursor() as cursor:
            if mode == 'replace':
                cursor.execute(f"DELETE FROM {table_name}")

            query = f"""
                INSERT INTO {table_name} 
                (product_number, upc, title, description, quantity_stock,
                 reorder_level, price, purchase_price, notes, image)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'images/default_placeholder.png')
            """

            try:
                for row in reader:
                    cursor.execute(query, (
                        row[0], row[1], row[2], row[3], 0,
                        int(row[4]), float(row[5]), float(row[6]),
                        row[7] if len(row) > 7 else ""
                    ))

                InventoryHistory.objects.create(
                    location=table_name,
                    user=request.user,
                    action="add",
                    details="Bulk uploaded classes. File = " + csv_file.name,
                )

                tenant = getattr(request, 'tenant', None)
                tenant_url = tenant.domain_url if tenant else tenant_url or ''
                return redirect(f"/{tenant_url}/invManage/")

            except Exception as e:
                return render(request, 'inventoryApp/csv_upload.html', {
                    'table_name': table_name,
                    'error_message': f"Error inserting data: {str(e)}"
                })

    return render(request, 'inventoryApp/csv_upload.html', {'table_name': table_name})




def download_inventory_template(request, tenant_url=None):
    # Create the HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="inventory_template.csv"'  

    # Create CSV writer
    writer = csv.writer(response)
    
    # Define the header row
    writer.writerow([
        "Product Number", "UPC", "Title", "Description", 
        "Reorder Level", "Price", "Purchase Price", "Notes"
    ])

    return response


def get_table_columns(table_name):
    with connection.cursor() as cursor:
        return [col.name for col in connection.introspection.get_table_description(cursor, table_name)]


def item_detail(request, table_name, item_id, tenant_url=None):
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", [item_id])
            row = cursor.fetchone()
            if not row:
                raise Http404("Item not found.")

            columns = ['id', 'product_number', 'upc', 'title', 'description', 'quantity_stock',
                       'reorder_level', 'price', 'purchase_price', 'image', 'notes']
            item = dict(zip(columns, row))

    except Exception as e:
        return HttpResponse(f"Error loading item: {e}", status=500)

    return render(request, "inventoryApp/item_detail.html", {
        "item": item,
        "table_name": table_name,
        "tenant_url": tenant_url
    })


def get_friendly_table_name(table_name):
    """Returns the friendly name of a table given its internal table_name."""
    try:
        entry = InvTable_Metadata.objects.get(table_name=table_name)
        return entry.table_friendly_name
    except InvTable_Metadata.DoesNotExist:
        return "Unknown Table"