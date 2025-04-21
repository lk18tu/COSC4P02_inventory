from django.test import TestCase
from django.apps import apps

class MessagingConfigTest(TestCase):
    def test_app_config(self):
        """Test that the messaging app is properly configured"""
        app_config = apps.get_app_config('messaging')
        self.assertEqual(app_config.name, 'inventory_track.messaging')
        self.assertEqual(app_config.verbose_name, 'Messaging')
