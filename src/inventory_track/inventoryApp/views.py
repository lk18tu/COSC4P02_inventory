
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import InvItem, InvTable_Metadata
from userauth.models import UserProfile
from django.db import connection, DatabaseError
from django.contrib import messages
from django.http import Http404
from django.conf import settings
import datetime
import csv, os


#table_name = f"testuser_invtable"  # Adjust based on the current user

# Create your views here.
def home(request):
    # Check if the user requested archived tables
    table_type = request.GET.get('view', 'inventory')  # Default to "inventory"

    inventory_tables = InvTable_Metadata.objects.filter(table_type=table_type).order_by('table_name')

    table_data = []
    for table in inventory_tables:
        table_name = table.table_name
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")  # Query the table
                columns = [col[0] for col in cursor.description]  # Get column names
                rows = cursor.fetchall()  # Get all rows

                table_data.append({
                    'table_name': table_name,
                    'columns': columns,
                    'rows': rows
                })
        except Exception as e:
            print(f"Error fetching data for {table_name}: {e}")
            continue  # Skip this table if there's an error

    return render(request, "inventoryHome.html", {
        "table_data": table_data,
        "MEDIA_URL": settings.MEDIA_URL,
        "current_view": table_type  # Pass the current view type to the template
    })

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

def add_item(request, table_name):
    if request.method == "POST":
        # Get all the data from the form
        product_number = request.POST.get('product_number')
        upc = request.POST.get('upc')
        title = request.POST.get('title')
        description = request.POST.get('description')
        quantity_stock = request.POST.get('quantity_stock')
        reorder_level = request.POST.get('reorder_level')
        price = request.POST.get('price')
        purchace_price = request.POST.get('purchace_price')
        notes = request.POST.get('notes')
        completed = 1 if request.POST.get('completed') == "on" else 0
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
                            purchace_price, notes, image
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [
                            product_number, upc, title, description, 
                            quantity_stock, reorder_level, price, 
                            purchace_price, notes, image_path
                        ]
                    )
                    return redirect("inventoryApp:home")
                else:
                    raise Http404(f"Table '{table_name}' does not exist.")

        except Exception as e:
            print(f"Error adding item to table {table_name}: {str(e)}")
            return redirect("inventoryApp:home")

    return render(request, "add_item.html", {"table_name": table_name})


def add_inventory(request):
    if request.method == "POST":
        new_table_name = request.POST.get("table_name")  # Get the table name from the form

        try:
            with connection.cursor() as cursor:
                # Create the table with an additional image column
                cursor.execute(f"""
                    CREATE TABLE {new_table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_number VARCHAR(100),
                        upc VARCHAR(255),
                        title VARCHAR(255),
                        description VARCHAR(255),
                        quantity_stock INT,
                        reorder_level INT,
                        price FLOAT(100, 2),
                        purchace_price FLOAT(100, 2),
                        image VARCHAR(255),
                        notes VARCHAR(255)
                    )
                """)
                # Add entry in the table_metadata table
                
                InvTable_Metadata.objects.create(table_name=new_table_name, table_type="inventory", table_location="Placeholder")

            return redirect("inventoryApp:home")
        except Exception as e:
            return HttpResponse(f"Error creating table: {e}", status=500)

    return render(request, "add_inventory.html")


def archive_table(request, table_name):
    if request.method == 'POST':  # Only allow POST request for safety
        try:
            # Get the table entry from metadata
            table_metadata = get_object_or_404(InvTable_Metadata, table_name=table_name)

            # Update table_type to 'archived_inventory'
            table_metadata.table_type = 'archived_inventory'
            table_metadata.save()

            print(f"Table '{table_name}' archived successfully.")
        except Exception as e:
            print(f"Error archiving table '{table_name}': {e}")

    return redirect("inventoryApp:home")  # Redirect back to home

def unarchive_table(request, table_name):
    if request.method == 'POST':  # Only allow POST request for safety
        try:
            # Get the table entry from metadata
            table_metadata = get_object_or_404(InvTable_Metadata, table_name=table_name)

            # Update table_type to 'archived_inventory'
            table_metadata.table_type = 'inventory'
            table_metadata.save()

            print(f"Table '{table_name}' unarchived successfully.")
        except Exception as e:
            print(f"Error unarchiving table '{table_name}': {e}")

    return redirect("inventoryApp:home")  # Redirect back to home



def delete_item(request, item_id, table_name):
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

                return redirect("inventoryApp:home")
            else:
                raise Http404(f"Table '{table_name}' does not exist.")
    except Exception as e:
        # Handle database errors or invalid queries
        print(f"Error deleting item: {str(e)}")
        return redirect("inventoryApp:home")


def edit_item(request, table_name, item_id):
    # Fetch the item details to pre-fill the form
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT * FROM {table_name} WHERE id = %s
            """, [item_id])
            item = cursor.fetchone()
            if not item:
                raise Http404(f"Item with ID {item_id} not found in table {table_name}.")
            
            # Extract fields dynamically based on the column names (you can adjust this as needed)
            # Assuming the columns are in this order: id, title, description, quantity_stock, etc.
            item_columns = ['id', 'title', 'description', 'quantity_stock', 'reorder_level', 'price', 'purchase_price', 'notes', 'completed']
            item_data = dict(zip(item_columns, item))

    except Exception as e:
        return Http404(f"Error fetching item: {str(e)}")
    
    if request.method == 'POST':
        # Get data from the form
        title = request.POST['title']
        description = request.POST['description']
        quantity_stock = request.POST['quantity_stock']
        reorder_level = request.POST['reorder_level']
        price = request.POST['price']
        purchase_price = request.POST['purchase_price']
        notes = request.POST['notes']
        completed = 'completed' in request.POST  # Checkbox handling

        # Handle file upload (optional, if needed)
        image = request.FILES.get('image', None)
        if image:
            # Handle image upload logic here
            pass
        
        try:
            # Update the item in the database
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET title = %s, description = %s, quantity_stock = %s, reorder_level = %s, 
                        price = %s, purchase_price = %s, notes = %s, completed = %s
                    WHERE id = %s
                """, [title, description, quantity_stock, reorder_level, price, purchase_price, notes, completed, item_id])

                # Log the action in the history table
                user_id = request.user.id
                cursor.execute(f"""
                    INSERT INTO history_inventoryhistory (action, timestamp, details, item_id, user_id)
                    VALUES ('update', NOW(), 'Updated item {item_id} in table {table_name}.', %s, %s)
                """, [item_id, user_id])

        except Exception as e:
            return Http404(f"Error updating item: {str(e)}")

        return redirect('inventoryApp:home')  # Redirect after successful update

    # Render the form with the current item data
    return render(request, 'edit_item.html', {'item': item_data, 'table_name': table_name})


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



def upload_csv(request, table_name):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        mode = request.POST.get('upload_mode')  # Fetch append/replace mode

        if not csv_file or not csv_file.name.endswith('.csv'):
            return HttpResponse("Invalid file format. Please upload a CSV file.", status=400)

        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        headers = next(reader)  # Read CSV headers

        expected_headers = ["Product Number", "UPC", "Title", "Description", "Quantity in Stock",
                            "Reorder Level", "Price", "Purchase Price", "Notes"]

        # Validate CSV headers
        if headers != expected_headers:
            return HttpResponse("Invalid CSV format. Ensure headers match the template.", status=400)

        with connection.cursor() as cursor:
            # Clear table if 'replace' mode is selected
            if mode == 'replace':
                cursor.execute(f"DELETE FROM {table_name}")

            # Insert new rows
            query = f"""
                INSERT INTO {table_name} 
                (product_number, upc, title, description, quantity_stock, reorder_level, price, purchace_price, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for row in reader:
                try:
                    cursor.execute(query, (
                        row[0],  # product_number
                        row[1],  # upc
                        row[2],  # title
                        row[3],  # description
                        int(row[4]),  # quantity_stock
                        int(row[5]),  # reorder_level
                        float(row[6]),  # price
                        float(row[7]),  # purchase_price
                        row[8] if len(row) > 8 else ""  # notes
                    ))
                except Exception as e:
                    return HttpResponse(f"Error inserting data: {str(e)}", status=400)

        return redirect('inventoryApp:home')

    return render(request, 'csv_upload.html', {'table_name': table_name})


def download_inventory_template(request):
    # Create the HTTP response with CSV content type
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_template.csv"'

    # Create CSV writer
    writer = csv.writer(response)
    
    # Define the header row
    writer.writerow(["Product Number", "UPC", "Title", "Description", "Quantity in Stock", 
                     "Reorder Level", "Price", "Purchase Price", "Notes"])

    return response


def get_table_columns(table_name):
    with connection.cursor() as cursor:
        return [col.name for col in connection.introspection.get_table_description(cursor, table_name)]


