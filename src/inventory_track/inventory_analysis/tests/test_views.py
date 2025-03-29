from django.test import TestCase
from django.urls import reverse
from inventory_analysis.models import InventoryItem

class InventoryViewsTest(TestCase):
    def setUp(self):
        InventoryItem.objects.create(name="Chair", category="Furniture", quantity=3)
        InventoryItem.objects.create(name="Notebook", category="Stationery", quantity=12)

    def test_inventory_chart_view_status_and_content(self):
        """Test inventory chart renders and contains image"""
        response = self.client.get(reverse("inventory_analysis:chart"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data:image/png;base64")

    def test_search_inventory_results(self):
        """Test that search returns matching inventory item"""
        response = self.client.get(reverse("inventory_analysis:search_inventory") + "?q=Chair")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chair")

    def test_search_inventory_empty_query(self):
        """Test search with no query returns all items"""
        response = self.client.get(reverse("inventory_analysis:search_inventory"))
        self.assertContains(response, "Notebook")
        self.assertContains(response, "Chair")
