from django.test import TestCase
from unittest.mock import patch
from django.urls import reverse

class LLMAdvisorTest(TestCase):
    @patch("inventory_analysis.views.requests.post")
    def test_llm_advisor_success(self, mock_post):
        """Mock successful response from DeepSeek API"""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "choices": [{"message": {"content": "You should restock."}}]
        }

        response = self.client.post(reverse("inventory_analysis:llm_advisor"), {"query": "Should I restock?"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("You should restock", response.json()["response"])

    def test_llm_advisor_get_method(self):
        """GET request should return advisor page"""
        response = self.client.get(reverse("inventory_analysis:llm_advisor"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI Inventory Advisor")

    @patch("inventory_analysis.views.requests.post")
    def test_llm_advisor_api_failure(self, mock_post):
        """Test DeepSeek failure case returns error message"""
        mock_post.return_value.status_code = 500
        mock_post.return_value.text = "Server error"
        response = self.client.post(reverse("inventory_analysis:llm_advisor"), {"query": "Any suggestion?"})
        self.assertIn("Error", response.json()["response"])
