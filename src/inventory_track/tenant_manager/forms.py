from django import forms
from .models import Tenant

class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['name', 'company_path', 'is_active']
        labels = {
            'name': 'Company Name',
            'company_path': 'URL Path',
            'is_active': 'Active',
        }
        help_texts = {
            'company_path': 'URL path identifier for the company (e.g., "acme" for /acme/)',
        }
        # We exclude owner, created_at, and db_name as they're handled in the view
        
    def clean_company_path(self):
        """
        Validate company_path to ensure it contains only letters, numbers and hyphens
        """
        company_path = self.cleaned_data.get('company_path')
        if company_path:
            # Convert to lowercase
            company_path = company_path.lower()
            
            # Check if it contains only valid characters
            import re
            if not re.match(r'^[a-z0-9-]+$', company_path):
                raise forms.ValidationError("Company path can only contain lowercase letters, numbers, and hyphens.")
            
            # Check if it starts with a letter
            if not company_path[0].isalpha():
                raise forms.ValidationError("Company path must start with a letter.")
                
        return company_path
