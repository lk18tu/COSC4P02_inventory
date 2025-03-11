from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from .models import InvItem, InvTable_Metadata
from django.db import connection, DatabaseError
from django.contrib import messages
from django.http import Http404
from django.conf import settings
import os

# table_name = f"testuser_invtable"  # Adjust based on the current user (commented out)

# Create your views here.
def home(request):
    # Query to get all inventory tables
    inventory_tables = InvTable_Metadata.objects.filter(table_type="inventory")

    table_data = []

    for table in inventory_tables:
        table_name = table.table_name

        # Fetch data from each inventory table
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")  # Query the table
                columns = [col[0] for col in cursor.description]  # Get column names
                rows = cursor.fetchall()  # Get all rows

                # Add the table's data to the list
                table_data.append({
                    'table_name': table_name,
                    'columns': columns,
                    'rows': rows
                })
        except Exception as e:
            print(f"Error fetching data for {table_name}: {e}")
            continue  # Continue with the next table if there's an error

    return render(request, "inventoryHome.html", {"table_data": table_data})

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

def add_item(request, table_name):
    if request.method == "POST":
        title = request.POST.get('title')
        quantity = request.POST.get('quantity')
        completed = request.POST.get('completed', False)
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
                        f"INSERT INTO {table_name} (title, quantity, completed, image) VALUES (%s, %s, %s, %s)",
                        [title, quantity, completed, image_path]
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
        table_name = request.POST.get("table_name")

        try:
            with connection.cursor() as cursor:
                # Create the table with an additional image column
                cursor.execute(f"""
                    CREATE TABLE {table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        title VARCHAR(255),
                        completed BOOLEAN,
                        quantity INT,
                        image VARCHAR(255)  # Store the image path as a string
                    )
                """)
                # Add entry in the table_metadata table
                InvTable_Metadata.objects.create(table_name=table_name, table_type="inventory", table_location="Unknown")

            return redirect("inventoryApp:home")
        except Exception as e:
            return HttpResponse(f"Error creating table: {e}", status=500)

    return render(request, "add_inventory.html")

def delete_item(request, item_id, table_name):
    try:
        with connection.cursor() as cursor:
            # Ensure the table exists before attempting to delete something from it
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()
            if result:
                cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", [item_id])
                return redirect("inventoryApp:home")
            else:
                raise Http404(f"Table '{table_name}' does not exist.")
    except Exception as e:
        # Handle database errors or invalid queries
        print(f"Error deleting item: {str(e)}")
        return redirect("inventoryApp:home")

def edit_item(request, item_id, table_name):
    try:
        with connection.cursor() as cursor:
            # Check if the table exists
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = cursor.fetchone()

            if result:
                # Fetch the item from the table that matches ID
                cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", [item_id])
                item = cursor.fetchone()

                if not item:
                    return redirect("inventoryApp:home")  # If item is not found, redirect to home

                if request.method == "POST":
                    # Process the form and update the item
                    new_title = request.POST.get("title")
                    new_quantity = request.POST.get("quantity")
                    new_completed = "completed" in request.POST  # Checkbox handling

                    # Perform the update in the database
                    cursor.execute(
                        f"UPDATE {table_name} SET title = %s, quantity = %s, completed = %s WHERE id = %s",
                        [new_title, new_quantity, new_completed, item_id]
                    )
                    return redirect("inventoryApp:home")  # After saving, redirect to the homepage

                # Render the edit form with the current item data
                return render(request, "edit_item.html", {"item": item})

            else:
                return redirect("inventoryApp:home")  # If table doesn't exist, redirect to home
    except Exception as e:
        print(f"Error: {e}")
        return redirect("inventoryApp:home")
