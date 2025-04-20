from django.shortcuts import render
from django.db.models import Q
from history.models import InventoryHistory  # Adjust import if needed
from django.core.paginator import Paginator

def history_view(request, tenant_url=None):
    """Displays inventory change history logs with search capability."""
    
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''

    logs = InventoryHistory.objects.all().order_by('-timestamp')  # Latest first

    search_query = request.GET.get('search')
    if search_query:
        logs = logs.filter(
            Q(details__icontains=search_query) |
            Q(action__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(timestamp__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(item_class_number__icontains=search_query) |
            Q(individual_item_number__icontains=search_query)
        )

    paginator = Paginator(logs, 8)  # Show 10 logs per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'history.html', {
        'logs': page_obj,
        'tenant_url': tenant_url
    })
