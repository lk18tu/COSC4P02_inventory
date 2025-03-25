from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from messaging.models import Contact

class ContactViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="u1", password="pwd")
        self.other = User.objects.create_user(username="u2", email="x@example.com")
        self.client.login(username="u1", password="pwd")

    def test_add_contact_by_username(self):
        """Test adding contact by username"""
        response = self.client.post(reverse("messaging:contacts"), {"contact": "u2"})
        self.assertEqual(Contact.objects.count(), 1)

    def test_add_contact_by_email(self):
        """Test adding contact by unique email"""
        response = self.client.post(reverse("messaging:contacts"), {"contact": "x@example.com"})
        self.assertEqual(Contact.objects.count(), 1)

    def test_add_self_forbidden(self):
        """User cannot add themselves as contact"""
        response = self.client.post(reverse("messaging:contacts"), {"contact": "u1"})
        self.assertContains(response, "You cannot add yourself")

    def test_delete_contact(self):
        """Test deleting contact"""
        contact = Contact.objects.create(user=self.user, contact=self.other)
        response = self.client.get(reverse("messaging:delete_contact", args=[contact.id]))
        self.assertEqual(Contact.objects.count(), 0)
