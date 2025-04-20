from django.shortcuts import render
from django.http import JsonResponse
import requests
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from .models import InventoryItem
from django.db.models import Sum
from django.db import connection
from dotenv import load_dotenv
import os

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
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT title, quantity_stock FROM {selected_table} ORDER BY quantity_stock ASC LIMIT 10")
                rows = cursor.fetchall()
                print("Feched")
                if rows:
                    inventory_info = "\n".join([f"{title}: {quantity_stock} in stock" for title, quantity_stock in rows])
        except Exception as e:
            print(f"error fetching {str(e)}")
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
    """
    Search through all dynamic inventory tables (from invApp) for items whose title
    matches the query. Each result will include the table name where the item is located.
    """
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    query = request.GET.get("q", "").strip()  # Get search query

    # Get a list of available inventory table names from your metadata
    inventory_tables = get_available_inventory_tables()
    results = []

    if query:
        for table in inventory_tables:
            try:
                with connection.cursor() as cursor:
                    # Use a LIKE query on the 'title' field in each dynamic table.
                    # Adjust the field name if your dynamic tables use a different column name.
                    cursor.execute(
                        f"SELECT title, quantity_stock FROM {table} WHERE title LIKE %s",
                        ['%' + query + '%']
                    )
                    rows = cursor.fetchall()
                    # Append each found row with its table name to the results list.
                    for row in rows:
                        results.append({
                            "title": row[0],
                            "total_quantity": row[1],
                            "table_name": table
                        })
            except Exception as e:
                print(f"Error searching table {table}: {e}")
                continue
    else:
        # If no query is provided, you might decide to return an empty result set.
        results = []

    return render(request, "inventory_analysis/search_results.html", {
        "results": results,
        "query": query,
        "tenant_url": tenant_url,
        "inventory_tables": inventory_tables
    })


def generate_inventory_level_chart(selected_table=None):
    """
    Generate an inventory level bar chart where each item's color is based on its individual reorder level.
    """
    try:
        if selected_table:
            with connection.cursor() as cursor:
                # Get title, quantity_stock, and reorder_level for each item
                cursor.execute(f"""
                    SELECT title, quantity_stock, reorder_level 
                    FROM `{selected_table}` 
                    ORDER BY quantity_stock ASC
                """)
                data = cursor.fetchall()

            if not data:
                return None

            names = [row[0] for row in data]
            quantities = np.array([row[1] for row in data])
            reorder_levels = np.array([row[2] for row in data])
        else:
            from inventoryApp.models import InvItem
            items = InvItem.objects.all()
            if not items:
                return None
            names = [item.title for item in items]
            quantities = np.array([item.quantity_stock for item in items])
            reorder_levels = np.array([item.reorder_level for item in items])

    except Exception as e:
        print("Error generating level chart:", e)
        return None

    # Dynamic color based on item-specific reorder level
    colors = np.where(
        quantities < reorder_levels, 'red',
        np.where(quantities == reorder_levels, 'orange', 'green')
    )

    plt.figure(figsize=(12, 6))
    bars = plt.bar(names, quantities, color=colors, edgecolor="black")

    for i, bar in enumerate(bars):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, str(quantities[i]),
                 ha='center', fontsize=10)
        # Optional: show reorder level as a dashed line per item
        plt.plot([bar.get_x(), bar.get_x() + bar.get_width()],
                 [reorder_levels[i], reorder_levels[i]],
                 linestyle='--', color='black', linewidth=1)

    plt.xticks(rotation=45)
    plt.title("Inventory Levels (Dynamic Reorder Alerts)", fontsize=14, fontweight="bold")
    plt.xlabel("Product Name")
    plt.ylabel("Stock Quantity")

    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, color='green', label='Above Reorder'),
        plt.Rectangle((0, 0), 1, 1, color='orange', label='At Reorder'),
        plt.Rectangle((0, 0), 1, 1, color='red', label='Below Reorder')
    ]
    plt.legend(handles=legend_handles)

    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return base64.b64encode(buf.read()).decode()



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

