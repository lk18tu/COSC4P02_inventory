from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import InventoryHistory

@login_required
def history_view(request, tenant_url=None):
    """Displays inventory change history logs."""
    tenant_url = request.tenant.domain_url if hasattr(request, 'tenant') else tenant_url or ''
    
    logs = InventoryHistory.objects.all().order_by('-timestamp')  # Sorted by time in descending order

    search_query = request.GET.get('search')
    if search_query:
        logs = logs.filter(details__icontains=search_query)  # Search in the details field

    return render(request, 'history.html', {
        'logs': logs,
        'tenant_url': tenant_url  # Add tenant_url to context
    })
