from django.test import TestCase
from inventory_analysis.models import InventoryItem

class InventoryItemModelTest(TestCase):
    def test_auto_assign_category_known_keyword(self):
        """Category should auto-assign 'Electronics' based on name"""
        item = InventoryItem.objects.create(name="Wireless Mouse", category="", quantity=10)
        self.assertEqual(item.category, "Electronics")

    def test_auto_assign_category_unknown(self):
        """Category should fallback to 'Uncategorized' if no match"""
        item = InventoryItem.objects.create(name="Mystery Gadget", category="", quantity=1)
        self.assertEqual(item.category, "Uncategorized")

    def test_str_representation(self):
        """Test __str__ method formatting"""
        item = InventoryItem.objects.create(name="Cable", category="Accessories", quantity=15)
        self.assertIn("Cable", str(item))
        self.assertIn("Accessories", str(item))
