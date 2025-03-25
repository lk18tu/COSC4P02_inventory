from django.test import TestCase, Client
from django.db import connection

class AddItemTest(TestCase):
    def setUp(self):
        """
        Set up a test database table dynamically.
        """
        self.client = Client()
        self.table_name = "test_inventory"

        with connection.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE {self.table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    product_number VARCHAR(255),
                    upc VARCHAR(255),
                    title VARCHAR(255),
                    description TEXT,
                    quantity_stock INT,
                    reorder_level INT,
                    price DECIMAL(10,2),
                    purchace_price DECIMAL(10,2),
                    notes TEXT,
                    image VARCHAR(255)
                )
            """)

    def test_add_item(self):
        """
        Test adding an item using the add_item view.
        """
        data = {
            "product_number": "12345",
            "upc": "987654321",
            "title": "Test Product",
            "description": "This is a test item.",
            "quantity_stock": 10,
            "reorder_level": 2,
            "price": 19.99,
            "purchace_price": 10.00,
            "notes": "Test note",
            "completed": "on"
        }

        response = self.client.post(f"/add_item/{self.table_name}/", data)

        # Check if redirected to home after success
        self.assertEqual(response.status_code, 302)

        # Verify that the item was inserted
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {self.table_name} WHERE title = %s", ["Test Product"])
            item = cursor.fetchone()
        
        self.assertIsNotNone(item, "Item was not added to the database")
        self.assertEqual(item[3], "Test Product", "Item title does not match")  # Assuming title is at index 3

    def tearDown(self):
        """
        Drop the test table after tests run.
        """
        with connection.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {self.table_name}")
