def tenant_context(request):
    """
    Add tenant information to the template context.
    """
    if hasattr(request, 'tenant'):
        return {
            'tenant': request.tenant,
            'tenant_url': request.tenant.domain_url,
        }
    return {}
