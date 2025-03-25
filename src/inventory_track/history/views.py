from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import InventoryHistory

@login_required
def history_view(request):
    logs = InventoryHistory.objects.all().order_by('-timestamp')  # 按时间倒序排序

 
    search_query = request.GET.get('search')
    if search_query:
        logs = logs.filter(details__icontains=search_query)  # ✅ 在 details 字段里搜索

    return render(request, 'history.html', {'logs': logs})
