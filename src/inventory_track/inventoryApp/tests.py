from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib import messages
from django.test import override_settings
from unittest.mock import patch
from tenant_manager.models import Tenant
from inventoryApp.models import InvTable_Metadata
from history.models import InventoryHistory
from django.db import connection
from django.http import Http404

class MockTenant:
    def __init__(self, name, domain_url):
        self.name = name
        self.domain_url = domain_url

class TenantRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = MockTenant('test_tenant', 'test-tenant')
        return self.get_response(request)

@patch('tenant_manager.middleware.TenantMiddleware', TenantRequestMiddleware)
class AddInventoryViewTests(TransactionTestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test-tenant',
            owner=self.user
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_add_inventory_blank_name(self):
        # Test adding inventory with blank table name
        url = reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'})
        response = self.client.post(url, {'table_name': ''})
        
        # Check that the response is successful (200 OK)
        self.assertEqual(response.status_code, 200)
        
        # Check that the form was rendered again (indicating validation failed)
        self.assertTemplateUsed(response, 'inventoryApp/add_inventory.html')
        
        # Check that an error message was added
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any("Error: Table name must be alphanumeric." in str(message) for message in messages_list))

    def test_add_inventory_invalid_characters(self):
        # Test adding inventory with invalid characters
        url = reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'})
        response = self.client.post(url, {'table_name': 'Test@Table#123!'})
        
        # Check that the response is successful (200 OK)
        self.assertEqual(response.status_code, 200)
        
        # Check that the form was rendered again (indicating validation failed)
        self.assertTemplateUsed(response, 'inventoryApp/add_inventory.html')
        
        # Check that an error message was added
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any("Error: Table name must be alphanumeric." in str(message) for message in messages_list))

    def test_add_inventory_success(self):
        # Test adding a new inventory table with a unique name
        url = reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'})
        response = self.client.post(url, {'table_name': 'TestInventorySuccess'})
        
        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))

        # Check that metadata entries were created
        classes_table_name = 'test_tenant_TestInventorySuccess_classes'
        items_table_name = 'test_tenant_TestInventorySuccess_items'

        # Verify metadata for classes table
        classes_metadata = InvTable_Metadata.objects.get(table_name=classes_table_name)
        self.assertEqual(classes_metadata.table_type, 'inventory')
        self.assertEqual(classes_metadata.table_friendly_name, 'TestInventorySuccess')
        self.assertEqual(classes_metadata.company_name, 'test_tenant')

        # Verify metadata for items table
        items_metadata = InvTable_Metadata.objects.get(table_name=items_table_name)
        self.assertEqual(items_metadata.table_type, 'inventory_individual_items')
        self.assertEqual(items_metadata.table_friendly_name, 'TestInventorySuccess')
        self.assertEqual(items_metadata.company_name, 'test_tenant')

        # Check that history entry was created
        history_entry = InventoryHistory.objects.filter(
            location='test_tenant_TestInventorySuccess',
            action='add'
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.details, 'Added Location: test_tenant_TestInventorySuccess')

        # Verify tables were created in database
        with connection.cursor() as cursor:
            # Check classes table exists
            cursor.execute("SHOW TABLES LIKE %s", [classes_table_name])
            self.assertIsNotNone(cursor.fetchone())

            # Check items table exists
            cursor.execute("SHOW TABLES LIKE %s", [items_table_name])
            self.assertIsNotNone(cursor.fetchone())

            # Check classes table structure
            cursor.execute(f"DESCRIBE {classes_table_name}")
            columns = {row[0] for row in cursor.fetchall()}
            expected_columns = {
                'id', 'product_number', 'upc', 'title', 'description',
                'quantity_stock', 'reorder_level', 'price', 'purchase_price',
                'image', 'notes'
            }
            self.assertEqual(columns, expected_columns)

            # Check items table structure
            cursor.execute(f"DESCRIBE {items_table_name}")
            columns = {row[0] for row in cursor.fetchall()}
            expected_columns = {
                'id', 'class_id', 'tracking_number', 'status', 'location',
                'destination_percentage', 'date_added', 'last_updated'
            }
            self.assertEqual(columns, expected_columns)

@patch('tenant_manager.middleware.TenantMiddleware', TenantRequestMiddleware)
class AddItemViewTests(TransactionTestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser2',  # Different username to avoid conflicts
            password='testpass123'
        )
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test-tenant',
            owner=self.user
        )
        self.client = Client()
        self.client.login(username='testuser2', password='testpass123')

        # Create a test inventory table with a unique name
        self.table_name = 'test_tenant_TestInventoryItems_classes'
        
        # Clean up any existing tables
        with connection.cursor() as cursor:
            # Drop items table first to avoid foreign key constraint issues
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name.replace('_classes', '_items')}")
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            # Clean up metadata table
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name}'")
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name.replace('_classes', '_items')}'")
        
        # Create new table
        response = self.client.post(reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'}), {'table_name': 'TestInventoryItems'})
        self.assertEqual(response.status_code, 302)  # Changed back to 302 since we expect a redirect

        # Verify the table was created
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW TABLES LIKE %s", [self.table_name])
            self.assertIsNotNone(cursor.fetchone(), "Table should exist after creation")

    def test_add_item_success(self):
        # Test adding a valid item
        url = reverse('inventoryApp:add_item', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name
        })
        response = self.client.post(url, {
            'product_number': 'TEST123',
            'title': 'Test Item',
            'reorder_level': '10',
            'description': 'Test Description',
            'price': '19.99',
            'purchase_price': '15.99',
            'notes': 'Test Notes'
        })
        
        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))

        # Verify the item was added to the database
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE product_number = %s", ['TEST123'])
            item = cursor.fetchone()
            self.assertIsNotNone(item)
            self.assertEqual(item[1], 'TEST123')  # product_number
            self.assertEqual(item[3], 'Test Item')  # title
            self.assertEqual(item[4], 'Test Description')  # description
            self.assertEqual(item[6], 10)  # reorder_level
            self.assertEqual(float(item[7]), 19.99)  # price
            self.assertEqual(float(item[8]), 15.99)  # purchase_price
            self.assertEqual(item[10], 'Test Notes')  # notes

        # Check that a history entry was created
        history_entry = InventoryHistory.objects.filter(
            location=self.table_name,
            action='add',
            item_class_number=item[0]  # id of the created item
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.details, 'Added item class: Test Item TEST123')

    def test_add_item_duplicate_product_number(self):
        # First add a valid item
        url = reverse('inventoryApp:add_item', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name
        })
        self.client.post(url, {
            'product_number': 'TEST123',
            'title': 'Test Item',
            'reorder_level': '10',
            'description': 'Test Description'
        })

        # Try to add another item with the same product number
        response = self.client.post(url, {
            'product_number': 'TEST123',  # Same product number
            'title': 'Different Item',
            'reorder_level': '20',
            'description': 'Different Description'
        })
        
        # Check that the response is successful (200 OK)
        self.assertEqual(response.status_code, 200)
        
        # Check that the form was rendered again (indicating validation failed)
        self.assertTemplateUsed(response, 'inventoryApp/add_item.html')
        
        # Check that an error message was added about duplicate product number
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any("That product number or UPC already exists." in str(message) for message in messages_list))

    def test_add_item_duplicate_upc(self):
        # First add a valid item
        url = reverse('inventoryApp:add_item', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name
        })
        self.client.post(url, {
            'product_number': 'TEST789',
            'title': 'Test Item',
            'reorder_level': '10',
            'description': 'Test Description',
            'upc': '123456789012'  # 12-digit UPC
        })

        # Try to add another item with the same UPC
        response = self.client.post(url, {
            'product_number': 'TEST456',  # Different product number
            'title': 'Different Item',
            'reorder_level': '20',
            'description': 'Different Description',
            'upc': '123456789012'  # Same UPC
        })
        
        # Check that the response is successful (200 OK)
        self.assertEqual(response.status_code, 200)
        
        # Check that the form was rendered again (indicating validation failed)
        self.assertTemplateUsed(response, 'inventoryApp/add_item.html')
        
        # Check that an error message was added about duplicate UPC
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any("That product number or UPC already exists." in str(message) for message in messages_list))

@patch('tenant_manager.middleware.TenantMiddleware', TenantRequestMiddleware)
class ArchiveTableTests(TransactionTestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser3',
            password='testpass123'
        )
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test-tenant',
            owner=self.user
        )
        self.client = Client()
        self.client.login(username='testuser3', password='testpass123')

        # Create a test inventory table with a unique name
        url = reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'})
        self.client.post(url, {'table_name': 'TestArchiveInventory'})
        self.table_name = 'test_tenant_TestArchiveInventory_classes'

    def test_archive_table_success(self):
        # Get the table metadata before archiving
        table_metadata = InvTable_Metadata.objects.get(table_name=self.table_name)
        self.assertEqual(table_metadata.table_type, 'inventory')

        # Archive the table
        url = reverse('inventoryApp:archive_table', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name
        })
        response = self.client.post(url)

        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))

        # Refresh the table metadata and check it's archived
        table_metadata.refresh_from_db()
        self.assertEqual(table_metadata.table_type, 'archived_inventory')

        # Check that a history entry was created
        history_entry = InventoryHistory.objects.filter(
            location=self.table_name,
            action='archive'
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.details, f"Archived Location: {self.table_name}")

    def test_unarchive_table_success(self):
        # First archive the table
        table_metadata = InvTable_Metadata.objects.get(table_name=self.table_name)
        table_metadata.table_type = 'archived_inventory'
        table_metadata.save()

        # Now test unarchiving
        url = reverse('inventoryApp:unarchive_table', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name
        })
        response = self.client.post(url)

        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))

        # Refresh the table metadata and check it's unarchived
        table_metadata.refresh_from_db()
        self.assertEqual(table_metadata.table_type, 'inventory')

        # Check that a history entry was created
        history_entry = InventoryHistory.objects.filter(
            location=self.table_name,
            action='unarchive'
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.details, f"Unarchived Location: {self.table_name}")

@patch('tenant_manager.middleware.TenantMiddleware', TenantRequestMiddleware)
class AddInventoryTests(TransactionTestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser4',
            password='testpass123'
        )
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test-tenant',
            owner=self.user
        )
        self.client = Client()
        self.client.login(username='testuser4', password='testpass123')

    def test_add_inventory_success(self):
        # Test adding a new inventory table
        url = reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'})
        response = self.client.post(url, {'table_name': 'TestInventory'})
        
        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))

        # Check that metadata entries were created
        classes_table_name = 'test_tenant_TestInventory_classes'
        items_table_name = 'test_tenant_TestInventory_items'

        # Verify metadata for classes table
        classes_metadata = InvTable_Metadata.objects.get(table_name=classes_table_name)
        self.assertEqual(classes_metadata.table_type, 'inventory')
        self.assertEqual(classes_metadata.table_friendly_name, 'TestInventory')
        self.assertEqual(classes_metadata.company_name, 'test_tenant')

        # Verify metadata for items table
        items_metadata = InvTable_Metadata.objects.get(table_name=items_table_name)
        self.assertEqual(items_metadata.table_type, 'inventory_individual_items')
        self.assertEqual(items_metadata.table_friendly_name, 'TestInventory')
        self.assertEqual(items_metadata.company_name, 'test_tenant')

        # Check that history entry was created
        history_entry = InventoryHistory.objects.filter(
            location='test_tenant_TestInventory',
            action='add'
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.details, 'Added Location: test_tenant_TestInventory')

        # Verify tables were created in database
        with connection.cursor() as cursor:
            # Check classes table exists
            cursor.execute("SHOW TABLES LIKE %s", [classes_table_name])
            self.assertIsNotNone(cursor.fetchone())

            # Check items table exists
            cursor.execute("SHOW TABLES LIKE %s", [items_table_name])
            self.assertIsNotNone(cursor.fetchone())

            # Check classes table structure
            cursor.execute(f"DESCRIBE {classes_table_name}")
            columns = {row[0] for row in cursor.fetchall()}
            expected_columns = {
                'id', 'product_number', 'upc', 'title', 'description',
                'quantity_stock', 'reorder_level', 'price', 'purchase_price',
                'image', 'notes'
            }
            self.assertEqual(columns, expected_columns)

            # Check items table structure
            cursor.execute(f"DESCRIBE {items_table_name}")
            columns = {row[0] for row in cursor.fetchall()}
            expected_columns = {
                'id', 'class_id', 'tracking_number', 'status', 'location',
                'destination_percentage', 'date_added', 'last_updated'
            }
            self.assertEqual(columns, expected_columns)

@patch('tenant_manager.middleware.TenantMiddleware', TenantRequestMiddleware)
class DeleteItemTests(TransactionTestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser5',
            password='testpass123'
        )
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test-tenant',
            owner=self.user
        )
        self.client = Client()
        self.client.login(username='testuser5', password='testpass123')

        # Create a test inventory table
        self.table_name = 'test_tenant_TestDeleteItem_classes'
        
        # Clean up any existing tables
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name.replace('_classes', '_items')}")
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            # Clean up metadata table
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name}'")
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name.replace('_classes', '_items')}'")
        
        # Create new table
        response = self.client.post(reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'}), {'table_name': 'TestDeleteItem'})
        self.assertEqual(response.status_code, 302)

        # Add a test item
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {self.table_name} 
                (product_number, title, description, reorder_level, price, purchase_price, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ['TEST123', 'Test Item', 'Test Description', 10, 19.99, 15.99, 'Test Notes'])
            self.item_id = cursor.lastrowid

    def test_delete_item_success(self):
        # First verify the item exists
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [self.item_id])
            self.assertIsNotNone(cursor.fetchone(), "Item should exist before deletion")

        # Delete the item
        url = reverse('inventoryApp:delete_item', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name,
            'item_id': self.item_id
        })
        response = self.client.post(url)

        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))

        # Verify the item was deleted
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [self.item_id])
            self.assertIsNone(cursor.fetchone(), "Item should be deleted")

        # Check that a history entry was created
        history_entry = InventoryHistory.objects.filter(
            location=self.table_name,
            action='delete',
            item_class_number=self.item_id
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.details, "Deleted item class: Test Item TEST123")

    def test_delete_item_not_found(self):
        # Try to delete an item that doesn't exist
        non_existent_id = 99999
        url = reverse('inventoryApp:delete_item', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name,
            'item_id': non_existent_id
        })
        
        # The view should return a 404 response
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

@patch('tenant_manager.middleware.TenantMiddleware', TenantRequestMiddleware)
class EditItemTests(TransactionTestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser6',
            password='testpass123'
        )
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test-tenant',
            owner=self.user
        )
        self.client = Client()
        self.client.login(username='testuser6', password='testpass123')

        # Create a test inventory table
        self.table_name = 'test_tenant_TestEditItem_classes'
        
        # Clean up any existing tables
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name.replace('_classes', '_items')}")
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            # Clean up metadata table
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name}'")
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name.replace('_classes', '_items')}'")
        
        # Create new table
        response = self.client.post(reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'}), {'table_name': 'TestEditItem'})
        self.assertEqual(response.status_code, 302)

        # Add a test item
        with connection.cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {self.table_name} 
                (product_number, title, description, reorder_level, price, purchase_price, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ['TEST123', 'Original Title', 'Original Description', 10, 19.99, 15.99, 'Original Notes'])
            self.item_id = cursor.lastrowid

    def test_edit_item_success(self):
        # First verify the original item exists
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [self.item_id])
            original_item = cursor.fetchone()
            self.assertIsNotNone(original_item, "Item should exist before editing")

        # Edit the item
        url = reverse('inventoryApp:edit_item', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name,
            'item_id': self.item_id
        })
        response = self.client.post(url, {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'reorder_level': '20',
            'price': '29.99',
            'purchase_price': '25.99',
            'notes': 'Updated Notes'
        })

        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))

        # Verify the item was updated
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [self.item_id])
            updated_item = cursor.fetchone()
            self.assertIsNotNone(updated_item, "Item should still exist after editing")
            
            # Check each field was updated correctly
            self.assertEqual(updated_item[3], 'Updated Title')  # title
            self.assertEqual(updated_item[4], 'Updated Description')  # description
            self.assertEqual(updated_item[6], 20)  # reorder_level
            self.assertEqual(float(updated_item[7]), 29.99)  # price
            self.assertEqual(float(updated_item[8]), 25.99)  # purchase_price
            self.assertEqual(updated_item[10], 'Updated Notes')  # notes

        # Check that a history entry was created
        history_entry = InventoryHistory.objects.filter(
            location=self.table_name,
            action='update',
            item_class_number=self.item_id
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        self.assertEqual(history_entry.details, "Updated Class: Updated Title")

    def test_edit_item_not_found(self):
        # Try to edit an item that doesn't exist
        non_existent_id = 99999
        url = reverse('inventoryApp:edit_item', kwargs={
            'tenant_url': 'test-tenant',
            'table_name': self.table_name,
            'item_id': non_existent_id
        })
        
        # The view should return a 404 response
        response = self.client.post(url, {
            'title': 'Updated Title',
            'description': 'Updated Description',
            'reorder_level': '20',
            'price': '29.99',
            'purchase_price': '25.99',
            'notes': 'Updated Notes'
        })
        self.assertEqual(response.status_code, 404)

@patch('tenant_manager.middleware.TenantMiddleware', TenantRequestMiddleware)
class UploadCSVTests(TransactionTestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser7',
            password='testpass123'
        )
        # Create a test tenant
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test-tenant',
            owner=self.user
        )
        self.client = Client()
        self.client.login(username='testuser7', password='testpass123')

        # Create a test inventory table
        self.table_name = 'test_tenant_TestUploadCSV_classes'
        
        # Clean up any existing tables
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name.replace('_classes', '_items')}")
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            # Clean up metadata table
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name}'")
            cursor.execute(f"DELETE FROM inventoryapp_invtable_metadata WHERE table_name = '{self.table_name.replace('_classes', '_items')}'")
        
        # Create new table
        response = self.client.post(reverse('inventoryApp:add_inventory', kwargs={'tenant_url': 'test-tenant'}), {'table_name': 'TestUploadCSV'})
        self.assertEqual(response.status_code, 302)

    def test_upload_csv_success(self):
        # Create a test CSV file
        csv_content = """Product Number,UPC,Title,Description,Reorder Level,Price,Purchase Price,Notes
TEST123,123456789012,Test Item 1,Test Description 1,10,19.99,15.99,Test Notes 1
TEST456,987654321098,Test Item 2,Test Description 2,20,29.99,25.99,Test Notes 2"""
        
        # Create a temporary file
        with open('test.csv', 'w') as f:
            f.write(csv_content)
        
        # Open the file for upload
        with open('test.csv', 'rb') as f:
            # Make the POST request
            url = reverse('inventoryApp:upload_csv', kwargs={
                'tenant_url': 'test-tenant',
                'table_name': self.table_name
            })
            response = self.client.post(url, {
                'csv_file': f,
                'upload_mode': 'append'
            })
        
        # Check that we were redirected
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith('/test-tenant/invManage/'))
        
        # Verify the items were added to the database
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name}")
            items = cursor.fetchall()
            self.assertEqual(len(items), 2)
            
            # Check first item
            self.assertEqual(items[0][1], 'TEST123')  # product_number
            self.assertEqual(items[0][2], '123456789012')  # upc
            self.assertEqual(items[0][3], 'Test Item 1')  # title
            self.assertEqual(items[0][4], 'Test Description 1')  # description
            self.assertEqual(items[0][6], 10)  # reorder_level
            self.assertEqual(float(items[0][7]), 19.99)  # price
            self.assertEqual(float(items[0][8]), 15.99)  # purchase_price
            self.assertEqual(items[0][10], 'Test Notes 1')  # notes
            
            # Check second item
            self.assertEqual(items[1][1], 'TEST456')  # product_number
            self.assertEqual(items[1][2], '987654321098')  # upc
            self.assertEqual(items[1][3], 'Test Item 2')  # title
            self.assertEqual(items[1][4], 'Test Description 2')  # description
            self.assertEqual(items[1][6], 20)  # reorder_level
            self.assertEqual(float(items[1][7]), 29.99)  # price
            self.assertEqual(float(items[1][8]), 25.99)  # purchase_price
            self.assertEqual(items[1][10], 'Test Notes 2')  # notes
        
        # Check that a history entry was created
        history_entry = InventoryHistory.objects.filter(
            location=self.table_name,
            action='add',
            details__startswith='Bulk uploaded classes'
        ).first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.user, self.user)
        
        # Clean up the test file
        import os
        os.remove('test.csv')

