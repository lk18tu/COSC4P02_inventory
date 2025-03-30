# Inventory Track - Multi-Tenant Inventory Management System

A comprehensive multi-tenant inventory management system that allows multiple companies to have their own isolated instances of the inventory management system. Each tenant gets a separate database and URL namespace for complete data isolation and security.

## Features

- **Multi-tenant architecture**: Complete data isolation between tenants
- **Inventory management**: Track stock levels, manage products, update quantities
- **User authentication**: Role-based access control (managers and employees)
- **Analytics**: Visualization of inventory data through charts and reports
- **Messaging system**: Internal communication between users
- **Notifications**: Real-time notifications for critical inventory events
- **History tracking**: Complete audit trail of inventory changes
- **AI Advisor**: Smart inventory recommendations
- **Search capabilities**: Fast inventory search and filtering
- **Dark mode UI**: Modern, responsive dark-themed interface

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up MySQL database as specified in settings.py
4. Run migrations:
   ```
   python manage.py migrate
   ```
5. Create a superuser for the main site:
   ```
   python manage.py createsuperuser
   ```
6. Run the development server:
   ```
   python manage.py runserver
   ```

## Tenant System Usage

### Creating a New Tenant
1. Register as a tenant owner at the main landing page
2. Login to the tenant dashboard
3. Create a new company from the dashboard
4. The system will automatically create and initialize the tenant's database

### Accessing Tenant Sites
Tenants can be accessed at URLs in this format:
```
http://localhost:8000/companyName/
```

Users can then navigate to specific features like:
- Dashboard: `/companyName/userauth/dashboard/`
- Inventory: `/companyName/invManage/`
- Stock Updates: `/companyName/updateStock/products/`
- Messaging: `/companyName/messaging/inbox/`
- Analytics: `/companyName/inventory_analysis/chart/`
- History: `/companyName/history/`

### Tenant User Management
- The first user created for a tenant is automatically assigned a manager role
- Subsequent users receive employee roles by default
- Managers have access to additional administrative features

## URL Structure

The application uses a path-based approach for multi-tenancy with the following pattern:
```
/<tenant_url>/<app_name>/<view_name>/
```

This structure ensures proper routing of requests to the appropriate tenant database and provides clean separation between tenant instances.

## Technical Implementation

The key components of this implementation are:

1. A `tenant_manager` app to handle tenant registration and management
2. A middleware to route requests to the appropriate tenant database
3. URL patterns with `tenant_url` parameter to support tenant-specific paths
4. Modified templates and views to work within tenant context
5. Database isolation through separate schemas for each tenant

Each tenant's data is completely isolated in its own database, ensuring security and scalability.

## Development Notes

- When creating new views, always include `tenant_url=None` parameter and handle it appropriately
- Use URL patterns that include the tenant URL when creating links between pages
- Test functionality across multiple tenants to ensure proper isolation

## Documentation

- [AI Inventory Advisor Guide](docs/ai_advisor.md)
