from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Notification

class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.tenant_url = 'testtenant'
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

        # Create a test notification
        self.notification = Notification.objects.create(
            user=self.user,
            message="Test notification",
            is_read=False
        )

    def test_notification_model_creation(self):
        """Ensure the notification is created properly"""
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(self.notification.message, "Test notification")
        self.assertFalse(self.notification.is_read)

    def test_view_notifications_returns_user_notifications(self):
        """Check if the view returns the correct notifications for the user"""
        url = reverse('notifications:view_notifications', args=[self.tenant_url])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test notification")

    def test_mark_notification_as_read(self):
        """Test that a notification can be marked as read"""
        url = reverse('notifications:mark_notification_read', args=[self.tenant_url, self.notification.id])
        self.client.get(url)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
