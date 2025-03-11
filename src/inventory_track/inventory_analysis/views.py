from django.shortcuts import render
from django.http import JsonResponse
import requests
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from .models import InventoryItem
from django.db.models import Sum


DEEPSEEK_API_KEY = "sk-a63cce70f55d493d99f9c0ad4993b4f9"

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

MODEL_NAME = "deepseek-chat"

def get_inventory_context():
    items = InventoryItem.objects.all().order_by("quantity")[:10]
    if not items:
        return "No inventory data available."

    inventory_info = "\n".join([f"{item.name}: {item.quantity} in stock" for item in items])
    context = f"Current Inventory Data:\n{inventory_info}\n\n"
    return context

def llm_advisor(request):
    if request.method == "POST":
        try:
            user_input = request.POST.get("query", "").strip()

            inventory_context = get_inventory_context()

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

    return render(request, "inventory_analysis/llm_advisor.html")


def search_inventory(request):
    """
    Display all inventory items by default and allow users to filter items using keywords.
    The search is case-insensitive and matches both name and category.
    Duplicate items will be merged, summing up their quantities.
    """
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

    return render(request, "inventory_analysis/search_results.html", {"results": merged_inventory, "query": query})

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


def inventory_chart(request):
    """
    Render the inventory chart page with different visualizations.
    """
    inventory_chart_image = generate_inventory_level_chart()  # Remove request argument
    inventory_pie_chart = generate_inventory_pie_chart()  # Generate pie chart

    return render(request, "inventory_analysis/inventory_chart.html", {
        "inventory_chart": inventory_chart_image,  # Fix variable name
        "inventory_pie_chart": inventory_pie_chart
    })
