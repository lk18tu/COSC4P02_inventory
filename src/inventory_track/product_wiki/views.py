import os
import requests
from dotenv import load_dotenv
from django.http import JsonResponse, Http404
from django.shortcuts import render
from django.core.cache import cache

# Load DeepSeek API key from .env file
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"


def generate_product_wiki(request, tenant_url=None):
    """
    API endpoint that returns AI-generated wiki content as JSON.
    Triggered via frontend JavaScript (AJAX).
    """
    product_name = request.GET.get("name", "")
    if not product_name:
        return JsonResponse({"error": "No product name provided."}, status=400)

    # Construct the prompt to send to DeepSeek
    prompt = f"""
    Generate a customer-friendly wiki page for the product '{product_name}'.
    Include: category, description, common use cases, and restocking suggestion.
    """

    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an assistant for product documentation."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Send request to DeepSeek API
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return JsonResponse({"response": content})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def view_product_wiki(request, tenant_url=None):
    """
    Render a standalone browser-accessible wiki page for a specific product.
    Uses cache to store generated content for 24 hours.
    """
    product_name = request.GET.get("name", "")
    if not product_name:
        raise Http404("Product name is required.")

    # Generate a unique cache key based on product name
    cache_key = f"wiki_{product_name.replace(' ', '_')}"

    # Return cached result if available
    cached_wiki = cache.get(cache_key)
    if cached_wiki:
        return render(request, "product_wiki/wiki_page.html", {
            "product_name": product_name,
            "wiki": cached_wiki,
            "tenant_url": tenant_url
        })

    # Construct the prompt for full-length content
    prompt = f"""
    Generate a full-length product wiki page for '{product_name}'.
    Include category, description, usage scenarios, and restocking advice.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an assistant that writes professional product wiki pages."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Request generation from DeepSeek
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Store result in cache for 24 hours (86400 seconds)
        cache.set(cache_key, content, timeout=60 * 60 * 24)
    except Exception as e:
        content = None

    return render(request, "product_wiki/wiki_page.html", {
        "product_name": product_name,
        "wiki": content,
        "tenant_url": tenant_url
    })
