# AI Documentation: Product Wiki Generation System

This document describes how the **AI-based Product Wiki** feature is integrated into the inventory management system using the DeepSeek large language model.

---

## 1. Overview

The AI Wiki module automatically generates documentation (wiki pages) for products in your inventory. It uses DeepSeek's `deepseek-chat` model to produce text based on a prompt. The system provides both an API for asynchronous responses (JSON) and a standalone HTML page for viewing wiki content directly in the browser.

**Key Features:**
- Automated product documentation via AI
- Separate JSON endpoint (`generate/`)
- Standalone wiki page rendering (`view/`)
- Server-side caching to avoid redundant requests
- Flexible to extend (markdown, PDF export, editing, etc.)

---

## 2. Architecture

### DeepSeek API Integration

- **Endpoint**: `https://api.deepseek.com/v1/chat/completions`
- **Model**: `deepseek-chat`
- **API Key**: Loaded from `.env` (`DEEPSEEK_API_KEY`)

Sample request body:

```
{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": "You are an assistant that writes product wiki pages."},
    {"role": "user", "content": "Generate a wiki for 'Wireless Mouse'..."}
  ],
  "temperature": 0.6,
  "max_tokens": 500
}
```
## 3. Functionality
### 3.1 JSON Endpoint: /product_wiki/generate/
- Usage: Typically triggered by front-end JavaScript (fetch() or AJAX)

- Request: GET with query param ?name=PRODUCT_NAME

- Response:

```
{
  "response": "Detailed wiki content..."
}
```
Example:
```
GET /test2/product_wiki/generate/?name=Wireless+Mouse
Implementation Snippet (views.py):
```
```
def generate_product_wiki(request, tenant_url=None):
    product_name = request.GET.get("name", "")
    if not product_name:
        return JsonResponse({"error": "No product name provided."}, status=400)

    # Prepare prompt
    prompt = f"Generate a customer-friendly wiki page for '{product_name}'..."

    data = {
        "model": "deepseek-chat",
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

    # Send request to DeepSeek
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        return JsonResponse({"response": content})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
```
### 3.2 Standalone Wiki Page: /product_wiki/view/?name=PRODUCT_NAME
Usage: Directly view AI wiki in browser

- Caches responses by product name

- Template: wiki_page.html

- Example:

```
GET /test2/product_wiki/view/?name=Laptop

```
Implementation Snippet (views.py):
```
def view_product_wiki(request, tenant_url=None):
    product_name = request.GET.get("name", "")
    if not product_name:
        raise Http404("Product name is required.")

    cache_key = f"wiki_{product_name.replace(' ', '_')}"

    # Check cache first
    cached_wiki = cache.get(cache_key)
    if cached_wiki:
        return render(request, "product_wiki/wiki_page.html", {
            "product_name": product_name,
            "wiki": cached_wiki,
            "tenant_url": tenant_url
        })

    # If not cached, request from DeepSeek
    prompt = f"Generate a full-length wiki for '{product_name}'..."

    payload = {
        "model": "deepseek-chat",
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
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        cache.set(cache_key, content, timeout=60 * 60 * 24)  # Cache for 24h
    except Exception as e:
        content = None

    return render(request, "product_wiki/wiki_page.html", {
        "product_name": product_name,
        "wiki": content,
        "tenant_url": tenant_url
    })
```
## 4. Templates
### 4.1 wiki_page.html
```
{% extends "base_company.html" %}
{% block title %}AI Product Wiki{% endblock %}

{% block content %}
<div class="container mt-5">
    <h2 class="text-white">Product Wiki: {{ product_name }}</h2>

    {% if wiki %}
        <div class="bg-gray-800 p-4 rounded mt-3">
            <pre class="text-gray-300" style="white-space: pre-wrap;">
{{ wiki }}
            </pre>
        </div>
    {% else %}
        <div class="alert alert-warning mt-3">
            Failed to generate wiki for this product.
        </div>
    {% endif %}
</div>
{% endblock %}
```
- Displays AI content or an error message

- Indented {{ wiki }} for better formatting (pre-wrap)

## 5. Caching
- Backend: Django’s built-in cache (cache.set, cache.get)

- imeout: 24 hours (configurable)

- Key: wiki_<product_name.replace(" ","_")>

This reduces repeated calls to the DeepSeek API, making page loads faster after the first generation.

## 6. Integration with inventoryApp
- Typically, you have an item_detail.html page. The user clicks a “Open Full Wiki Page” button or link:
```
<a href="/{{ tenant_url }}/product_wiki/view/?name={{ item.title }}">
    Open AI Wiki
</a>
```
- Or you can fetch JSON via generate/ and display the result inline.