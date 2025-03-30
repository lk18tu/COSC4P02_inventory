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
    Display all inventory items by default and allow users to filter items using keywords.
    The search is case-insensitive and matches both name and category.
    Duplicate items will be merged, summing up their quantities.
    """
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    query = request.GET.get("q", "").strip()  # Get search query from request

    if query:
        # Search items by name or category
        items = InventoryItem.objects.filter(
            name__icontains=query
        ) | InventoryItem.objects.filter(
            category__icontains=query
        )
    else:
        # If no search query is provided, fetch all items
        items = InventoryItem.objects.all()

    # Aggregate items by name and category
    merged_inventory = (
        items.values("name", "category")  # Group by name and category
        .annotate(total_quantity=Sum("quantity"))  # Sum up quantities
        .order_by("name")  # Sort alphabetically
    )

    return render(request, "inventory_analysis/search_results.html", {
        "results": merged_inventory, 
        "query": query,
        "tenant_url": tenant_url  # Add tenant_url to context
    })

def generate_inventory_level_chart():
    """
    Generate an inventory level bar chart with a reorder alert threshold.
    """
    items = InventoryItem.objects.all()
    
    if not items:
        return None

    names = [item.name for item in items]
    quantities = np.array([item.quantity for item in items])

    # Define colors (low stock: red, medium: yellow, sufficient: green)
    colors = np.where(quantities < 5, 'red', np.where(quantities <= 15, 'yellow', 'green'))

    # Generate the inventory level bar chart
    plt.figure(figsize=(12, 6))
    bars = plt.bar(names, quantities, color=colors, edgecolor="black")
    plt.axhline(y=5, color='black', linestyle='--', linewidth=1.5, label="Reorder Threshold (5 units)")

    for bar, qty in zip(bars, quantities):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, str(qty), ha='center', fontsize=10)

    plt.xticks(rotation=45)
    plt.title("Inventory Levels & Reorder Alerts", fontsize=14, fontweight="bold")
    plt.xlabel("Product Name")
    plt.ylabel("Stock Quantity")
    plt.legend()

    # Convert the chart to Base64
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

def generate_inventory_pie_chart():
    """
    Generate a pie chart representing the percentage of each product's stock.
    """
    items = InventoryItem.objects.all()
    
    if not items:
        return None

    names = [item.name for item in items]
    quantities = np.array([item.quantity for item in items])

    # Ignore items with zero stock
    if sum(quantities) == 0:
        return None  

    # Generate pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(
        quantities,
        labels=names,
        autopct='%1.1f%%',
        startangle=140,
        colors=plt.cm.Paired.colors
    )
    plt.title("Inventory Distribution")

    # Save the chart as a Base64 image
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def inventory_chart(request, tenant_url=None):
    """
    Render the inventory chart page with different visualizations.
    """
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    inventory_chart_image = generate_inventory_level_chart()  # Remove request argument
    inventory_pie_chart = generate_inventory_pie_chart()  # Generate pie chart

    return render(request, "inventory_analysis/inventory_chart.html", {
        "inventory_chart": inventory_chart_image,
        "inventory_pie_chart": inventory_pie_chart,
        "tenant_url": tenant_url  # Add tenant_url to context
    })
