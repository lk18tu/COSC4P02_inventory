from django.test import TestCase
from django.contrib.auth.models import User
from inventoryApp.models import InvItem
from .models import InventoryHistory

class InventoryHistoryTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass1234')
        self.item = InvItem.objects.create(title='Test Item', quantity=10)

    def test_log_creation(self):
        log = InventoryHistory.objects.create(
            item=self.item,  
            user=self.user,
            action='ADD',
            details='Initial test log entry'
        )
        self.assertEqual(log.item, self.item)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'ADD')
        self.assertEqual(log.details, 'Initial test log entry')
