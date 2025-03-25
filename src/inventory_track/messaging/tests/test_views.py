from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from messaging.models import Message

class MessagingViewTest(TestCase):
    def setUp(self):
        """Set up two users and login user1"""
        self.client = Client()
        self.user1 = User.objects.create_user(username="u1", password="pwd")
        self.user2 = User.objects.create_user(username="u2", email="u2@example.com", password="pwd")
        self.client.login(username="u1", password="pwd")

    def test_send_message_by_username(self):
        """Test sending message using username"""
        response = self.client.post(reverse("messaging:send_message"), {
            "recipient": "u2",
            "subject": "Hello",
            "content": "Hi there!"
        })
        self.assertEqual(Message.objects.count(), 1)
        self.assertRedirects(response, reverse("messaging:inbox"))

    def test_send_message_by_email(self):
        """Test sending message using email"""
        response = self.client.post(reverse("messaging:send_message"), {
            "recipient": "u2@example.com",
            "subject": "Email Test",
            "content": "Email routing"
        })
        self.assertEqual(Message.objects.count(), 1)

    def test_inbox_display(self):
        """Test inbox displays user's received messages by subject"""
        Message.objects.create(
            sender=self.user2,
            recipient=self.user1,
            subject="Test Subject",
            content="Hidden Content"
        )
        response = self.client.get(reverse("messaging:inbox"))
        self.assertContains(response, "Test Subject")

    def test_read_marks_as_read(self):
        """Test reading message marks it as read"""
        msg = Message.objects.create(sender=self.user2, recipient=self.user1, content="read test")
        self.assertFalse(msg.read)
        response = self.client.get(reverse("messaging:read_message", args=[msg.id]))
        msg.refresh_from_db()
        self.assertTrue(msg.read)
