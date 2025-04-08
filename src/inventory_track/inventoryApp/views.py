from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import InvItem, InvTable_Metadata
from userauth.models import UserProfile
from django.db import connection, DatabaseError
from django.contrib import messages
from django.http import Http404
from django.conf import settings
import datetime
import csv, os
from tenant_manager.utils import tenant_context


#table_name = f"testuser_invtable"  # Adjust based on the current user

# Create your views here.
def home(request, tenant_url=None):
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    # Get all inventory tables
    inventory_tables = InvTable_Metadata.objects.filter(table_type="inventory")
    
    # Get archived tables
    archived_tables = InvTable_Metadata.objects.filter(table_type="archived_inventory")
    
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
    if request.method == "POST":
        # Get all the data from the form
        product_number = request.POST.get('product_number')
        upc = request.POST.get('upc')
        title = request.POST.get('title')
        description = request.POST.get('description')
        quantity_stock = request.POST.get('quantity_stock')
        reorder_level = request.POST.get('reorder_level')
        price = request.POST.get('price')
        purchase_price = request.POST.get('purchase_price')
        notes = request.POST.get('notes')
        image = request.FILES.get('image')  # Get the uploaded image

        try:
            with connection.cursor() as cursor:
                # Check if the table exists
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                result = cursor.fetchone()

                if result:
                    # Handle image upload
                    image_path = None
                    if image:
                        # Save the image to the media directory
                        image_path = os.path.join('inventory_images', image.name)
                        full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'wb+') as destination:
                            for chunk in image.chunks():
                                destination.write(chunk)
                    else:
                        # Use a default placeholder if no image is provided
                        image_path = 'images/default_placeholder.png'

                    # Insert the item into the dynamic table
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
                            product_number, upc, title, description, 
                            0, reorder_level, price, 
                            purchase_price, notes, image_path
                        ]
                    )

                    # log change
                    log_inventory_action("ADD", "Added item: "+title, product_number, 0000)
                    
                    # Get tenant URL for redirect
                    tenant = getattr(request, 'tenant', None)
                    tenant_url = tenant.domain_url if tenant else tenant_url or ''
                    return redirect(f"/{tenant_url}/invManage/")
                else:
                    raise Http404(f"Table '{table_name}' does not exist.")

        except Exception as e:
            print(f"Error adding item to table {table_name}: {str(e)}")
            tenant = getattr(request, 'tenant', None)
            tenant_url = tenant.domain_url if tenant else tenant_url or ''
            return redirect(f"/{tenant_url}/invManage/")

    return render(request, "inventoryApp/add_item.html", {"table_name": table_name})


from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect, render
from .models import InvTable_Metadata  # Ensure this is imported
from .utils import log_inventory_action  # Assuming this is a custom function

def add_inventory(request, tenant_url=None):
    tenant = getattr(request, 'tenant', None)
    
    if request.method == "POST":
        Friendly_new_table_name = request.POST.get("table_name")  # Get the table name from the form
        new_table_name = Friendly_new_table_name.replace(" ", "") #deletes spaces to allow for table name creation (SQL doest allow spaces)


        # Basic validation to prevent SQL injection (simplified)
        if not new_table_name.isalnum():  # Allow only alphanumeric characters
            return HttpResponse("Error: Table name must be alphanumeric", status=400)

        try:
            # No need to switch contexts - just use the current connection
            with connection.cursor() as cursor:
                # Debug the current database connection
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                print(f"Creating table {new_table_name} in database {current_db}")
                
                # Create the table with corrected spelling
                cursor.execute(f"""
                    CREATE TABLE `{new_table_name}_classes` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_number VARCHAR(100),
                        upc VARCHAR(255),
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

                # Create the individual item tracking table
                cursor.execute(f"""
                    CREATE TABLE `{new_table_name}_items` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        class_id INT,
                        tracking_number VARCHAR(100) UNIQUE,
                        status VARCHAR(20),
                        location VARCHAR(100),
                        date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (class_id) REFERENCES {new_table_name}_classes(id)
                    )
                """)

                # Add entry in the table_metadata table
                InvTable_Metadata.objects.create(
                    table_name=new_table_name+"_classes",
                    table_type="inventory",
                    table_friendly_name = Friendly_new_table_name
                )

            tenant_url = tenant.domain_url if tenant else ''
            return redirect(f"/{tenant_url}/invManage/")
        except Exception as e:
            print(f"Error creating inventory table: {str(e)}")
            return HttpResponse(f"Error: {str(e)}", status=500)
    
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
            log_inventory_action("ARCHIVED INV", "Archived: "+table_name, 0 , 0000 )
            
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
    try:
        with connection.cursor() as cursor:
            # Ensure the table exists before attempting to delete something from it
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()

            if result:
                # Delete the item from the table
                cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", [item_id])

                # get username for logging
                user_profile = UserProfile.objects.get(user=request.user)
                username = user_profile.user.username

                # log change
                log_inventory_action("DELETE", "N/A", item_id, 0000 )

                # Get tenant URL for redirect
                tenant = getattr(request, 'tenant', None)
                tenant_url = tenant.domain_url if tenant else tenant_url or ''
                return redirect(f"/{tenant_url}/invManage/")
            else:
                raise Http404(f"Table '{table_name}' does not exist.")
    except Exception as e:
        # Handle database errors or invalid queries
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

        except Exception as e:
            return HttpResponse(f"<h1>Error updating item:</h1><p>{str(e)}</p>", status=500)

        # Redirect after saving
        tenant = getattr(request, 'tenant', None)
        tenant_url = tenant.domain_url if tenant else tenant_url or ''
        return redirect(f"/{tenant_url}/invManage/")

    return render(request, 'inventoryApp/edit_item.html', {'item': item_data, 'table_name': table_name})


def log_inventory_action(action, details, item_id, user_id):
    """
    Logs inventory actions (DELETE, UPDATE, INSERT, etc.) to the history table.
    
    :param action: The type of action performed (DELETE, UPDATE, INSERT)
    :param details: A string describing what was changed
    :param item_id: The ID of the affected item
    :param user_id: The ID of the user who performed the action
    """
    try:
        timestamp = datetime.datetime.now()  # Ensure datetime is used properly
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO history_inventoryhistory (action, timestamp, details, item, user)
                VALUES (%s, %s, %s, %s, %s)
            """, [action, timestamp, details, item_id, user_id])
    except Exception as e:
        print(f"Error logging action: {str(e)}")



def upload_csv(request, table_name, tenant_url=None):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        mode = request.POST.get('upload_mode')  # Fetch append/replace mode

        if not csv_file or not csv_file.name.endswith('.csv'):
            return HttpResponse("Invalid file format. Please upload a CSV file.", status=400)

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        headers = next(reader)  # Read CSV headers

        # Removed Quantity in Stock from expected headers
        expected_headers = ["Product Number", "UPC", "Title", "Description",
                            "Reorder Level", "Price", "Purchase Price", "Notes"]

        if headers != expected_headers:
            return HttpResponse("Invalid CSV format. Ensure headers match the template.", status=400)

        with connection.cursor() as cursor:
            if mode == 'replace':
                cursor.execute(f"DELETE FROM {table_name}")

            # Add quantity_stock (set to 0) in the insert
            query = f"""
                INSERT INTO {table_name} 
                (product_number, upc, title, description, quantity_stock,
                 reorder_level, price, purchase_price, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            for row in reader:
                try:
                    cursor.execute(query, (
                        row[0],  # product_number
                        row[1],  # upc
                        row[2],  # title
                        row[3],  # description
                        0,       # quantity_stock hardcoded to 0
                        int(row[4]),  # reorder_level
                        float(row[5]),  # price
                        float(row[6]),  # purchase_price
                        row[7] if len(row) > 7 else ""  # notes
                    ))
                except Exception as e:
                    return HttpResponse(f"Error inserting data: {str(e)}", status=400)

            log_inventory_action("BULK", f"Uploaded: {csv_file.name} To {table_name}. Mode = {mode}", 0, 0000)

            tenant = getattr(request, 'tenant', None)
            tenant_url = tenant.domain_url if tenant else tenant_url or ''
            return redirect(f"/{tenant_url}/invManage/")

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
