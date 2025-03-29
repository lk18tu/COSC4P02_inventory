from django.test import TestCase, Client
from django.contrib.auth.models import User
from messaging.models import Message, Contact

class MessageModelTest(TestCase):
    def test_mark_as_read(self):
        """Test mark_as_read() sets read=True"""
        user1 = User.objects.create_user(username="u1")
        user2 = User.objects.create_user(username="u2")
        message = Message.objects.create(sender=user1, recipient=user2, content="Test")
        self.assertFalse(message.read)
        message.mark_as_read()
        self.assertTrue(message.read)

class ContactModelTest(TestCase):
    def test_contact_str(self):
        """Test __str__ method of Contact"""
        u1 = User.objects.create_user(username="a")
        u2 = User.objects.create_user(username="b")
        c = Contact.objects.create(user=u1, contact=u2)
        self.assertEqual(str(c), "a -> b")
