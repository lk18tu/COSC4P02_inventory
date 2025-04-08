from django.shortcuts import render
from django.http import JsonResponse
import requests
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from inventoryApp.models import InvItem as InventoryItem
from django.db.models import Sum
from django.db import connection
from dotenv import load_dotenv
import os

from inventoryApp.models import InvItem

# Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"

def get_available_inventory_tables():
    """Retrieve available inventory table names from inventoryapp_invtable_metadata where table_type='inventory'."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT table_name FROM inventoryapp_invtable_metadata WHERE table_type = 'inventory'")
            tables = [row[0] for row in cursor.fetchall()]  # Extract table names
        return tables
    except Exception as e:
        print(f"Error fetching inventory tables: {e}")
        return []

def get_inventory_context(selected_table):
    with connection.cursor() as cursor:
        try:
            # Note: InvItem uses 'quantity' (not 'quantity_stock') and 'title'
            cursor.execute(f"SELECT title, quantity FROM {selected_table} ORDER BY quantity ASC LIMIT 10")
            rows = cursor.fetchall()
            if rows:
                inventory_info = "\n".join([f"{title}: {quantity} in stock" for title, quantity in rows])
            else:
                inventory_info = "No inventory data available."
        except Exception as e:
            print(f"Error fetching inventory: {str(e)}")
            inventory_info = f"Error fetching inventory: {str(e)}"
    context = f"Current Inventory Data:\n{inventory_info}\n\n"
    return context

def llm_advisor(request, tenant_url=None):
    """Provides AI-powered inventory advice based on user queries."""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    inventory_tables = get_available_inventory_tables()  # Fetch table names
    selected_table = request.GET.get("table") or request.POST.get("table") or (inventory_tables[0] if inventory_tables else None)

    if request.method == "POST" and selected_table:
        try:
            user_input = request.POST.get("query", "").strip()

           
            inventory_context = get_inventory_context(selected_table) if selected_table else "No inventory table selected."

            data = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": "You are an AI assistant that specializes in inventory management. Analyze the given inventory data and provide actionable restocking advice."},
                    {"role": "system", "content": inventory_context}, 
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7
            }

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }

            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)

            if response.status_code == 200:
                result = response.json()
                llm_response = result["choices"][0]["message"]["content"]
            else:
                llm_response = f"Error: {response.status_code} - {response.text}"

            return JsonResponse({"response": llm_response})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return render(request, "inventory_analysis/llm_advisor.html", {
        "inventory_tables": inventory_tables,
        "selected_table": selected_table,
        "tenant_url": tenant_url  # Add tenant_url to context
    })


def search_inventory(request, tenant_url=None):
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    query = request.GET.get("q", "").strip()

    if query:
        # Search items by title (case-insensitive) and aggregate in the same step if not using union
        items = InventoryItem.objects.filter(title__icontains=query).values("title").annotate(total_quantity=Sum("quantity")).order_by("title")
    else:
        # If no search query is provided, fetch and aggregate all items
        items = InventoryItem.objects.all().values("title").annotate(total_quantity=Sum("quantity")).order_by("title")

    return render(request, "inventory_analysis/search_results.html", {
        "results": items,
        "query": query,
        "tenant_url": tenant_url
    })



def generate_inventory_level_chart(selected_table=None):
    """
    Generate an inventory level bar chart with a reorder alert threshold using data from the
    specified dynamic table (if provided) or the default InvItem model data.
    """
    try:
        if selected_table:
            with connection.cursor() as cursor:
                # Query using dynamic table; InvItem in your invApp uses 'title' and 'quantity_stock'
                cursor.execute(f"SELECT title, quantity_stock FROM {selected_table} ORDER BY quantity_stock ASC")
                data = cursor.fetchall()
            if not data:
                return None
            names = [row[0] for row in data]
            quantities = np.array([row[1] for row in data])
        else:
            # Default: use the InvItem model from inventoryApp
            from inventoryApp.models import InvItem
            items = InvItem.objects.all()
            if not items:
                return None
            names = [item.title for item in items]
            quantities = np.array([item.quantity for item in items])
    except Exception as e:
        print("Error generating level chart:", e)
        return None

    # Define colors for each stock level
    colors = np.where(quantities < 5, 'red', np.where(quantities <= 15, 'yellow', 'green'))

    plt.figure(figsize=(12, 6))
    bars = plt.bar(names, quantities, color=colors, edgecolor="black")
    plt.axhline(y=5, color='black', linestyle='--', linewidth=1.5, label="Reorder Threshold (5 units)")

    for bar, qty in zip(bars, quantities):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, str(qty),
                 ha='center', fontsize=10)

    plt.xticks(rotation=45)
    plt.title("Inventory Levels & Reorder Alerts", fontsize=14, fontweight="bold")
    plt.xlabel("Product Name")
    plt.ylabel("Stock Quantity")
    plt.legend()

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()  # Free memory by closing the figure
    return base64.b64encode(buf.read()).decode()



# In inventory_analysis/views.py

def generate_inventory_pie_chart(selected_table=None):
    """
    Generate a pie chart representing the percentage of each product's stock.
    If selected_table is provided, fetch data from that dynamic table; otherwise, use the default InvItem model.
    """
    try:
        if selected_table:
            with connection.cursor() as cursor:
                # Use the dynamic table's columns: 'title' and 'quantity_stock'
                cursor.execute(f"SELECT title, quantity_stock FROM {selected_table}")
                rows = cursor.fetchall()
            if not rows:
                return None
            names = [row[0] for row in rows]
            quantities = np.array([row[1] for row in rows])
        else:
            from inventoryApp.models import InvItem
            items = InvItem.objects.all()
            if not items:
                return None
            names = [item.title for item in items]
            quantities = np.array([item.quantity for item in items])
    except Exception as e:
        print(f"Error fetching data for pie chart: {e}")
        return None

    if sum(quantities) == 0:
        return None

    plt.figure(figsize=(8, 8))
    plt.pie(
        quantities,
        labels=names,
        autopct='%1.1f%%',
        startangle=140,
        colors=plt.cm.Paired.colors
    )
    plt.title("Inventory Distribution")
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()  # Free memory
    return base64.b64encode(buf.read()).decode()



def inventory_chart(request, tenant_url=None):
    """
    Render the inventory chart page using data from a dynamic table.
    The table is selected via a GET parameter (or defaults to the first available table).
    """
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    inventory_tables = get_available_inventory_tables()
    selected_table = request.GET.get("table") or (inventory_tables[0] if inventory_tables else None)

    inventory_chart_image = generate_inventory_level_chart(selected_table) if selected_table else None
    inventory_pie_chart = generate_inventory_pie_chart(selected_table) if selected_table else None

    return render(request, "inventory_analysis/inventory_chart.html", {
        "inventory_chart": inventory_chart_image,
        "inventory_pie_chart": inventory_pie_chart,
        "selected_table": selected_table,
        "inventory_tables": inventory_tables,
        "tenant_url": tenant_url
    })

