from django.test import TestCase
from .models import InventoryItem

class InventoryAnalysisTests(TestCase):
    def setUp(self):
        InventoryItem.objects.create(name="Test Item", category="Test", quantity=5)

    def test_inventory_search(self):
        response = self.client.get("/inventory_analysis/search/?q=Test Item")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Item")

    def test_llm_advisor(self):
        response = self.client.post("/inventory_analysis/advisor/", {"query": "Should I order more?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("response", response.json())

    def test_inventory_chart(self):
        response = self.client.get("/inventory_analysis/chart/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data:image/png;base64,")
