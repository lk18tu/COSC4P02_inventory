from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core import mail
from django.conf import settings
import pytz
import datetime
from .models import UserProfile, Notification
from unittest.mock import patch

class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword123',
        }
        self.user_data_unmatching_password = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123',
            'confirm_password': 'TestPassword456',
        }

    def test_user_registration_view_GET(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userauth/register.html')

    def test_user_registration_valid_POST(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(UserProfile.objects.first().user_type, 'employee')  # Default type
        self.assertRedirects(response, self.login_url)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Registration successful" in str(message) for message in messages))

    def test_user_registration_unmatching_password(self):
        response = self.client.post(self.register_url, self.user_data_unmatching_password)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 0)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Passwords do not match" in str(message) for message in messages))

    def test_user_registration_existing_username(self):
        # Create a user first
        User.objects.create_user(username='testuser', email='existing@example.com', password='TestPassword123')
       
        # Try to register with the same username
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)  # No new user created
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("User already exists" in str(message) for message in messages))

    def test_user_registration_existing_email(self):
        # Create a user first
        User.objects.create_user(username='existinguser', email='test@example.com', password='TestPassword123')
       
        # Try to register with the same email but different username
        data = self.user_data.copy()
        data['username'] = 'newuser'
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 1)  # No new user created
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Email already exists" in str(message) for message in messages))


class UserLoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.dashboard_url = reverse('dashboard')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )
        self.login_data = {
            'username': 'testuser',
            'password': 'TestPassword123'
        }
        self.invalid_login_data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }

    def test_login_view_GET(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userauth/login.html')

    def test_login_valid_credentials(self):
        response = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertRedirects(response, self.dashboard_url)
        # Check that UserProfile is created if it doesn't exist
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_login_invalid_credentials(self):
        response = self.client.post(self.login_url, self.invalid_login_data)
        self.assertEqual(response.status_code, 200)  # Stay on the same page
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Username or password does not match" in str(message) for message in messages))


class UserLogoutTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('logout')
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )

    def test_logout_view(self):
        # Login first
        self.client.login(username='testuser', password='TestPassword123')
       
        # Then logout
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        self.assertRedirects(response, self.login_url)
       
        # Verify user is logged out by trying to access a protected page
        dashboard_url = reverse('dashboard')
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirects to login


class DashboardTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )
        self.profile = UserProfile.objects.create(user=self.user, user_type='employee')
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='ManagerPass123'
        )
        self.manager_profile = UserProfile.objects.create(user=self.manager, user_type='manager')
       
        # Create some notifications
        Notification.objects.create(user=self.user, message="Test notification 1", is_read=False)
        Notification.objects.create(user=self.user, message="Test notification 2", is_read=False)
        Notification.objects.create(user=self.user, message="Test notification 3", is_read=True)

     

    @patch('inventory_analysis.views.generate_inventory_pie_chart')
    def test_dashboard_manager_view(self, mock_pie_chart):
        mock_pie_chart.return_value = "mock_chart_data"
        self.client.login(username='manager', password='ManagerPass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_manager'])


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )
        self.employee_profile = UserProfile.objects.create(
            user=self.user,
            user_type='employee'
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='ManagerPass123'
        )
        self.manager_profile = UserProfile.objects.create(
            user=self.manager,
            user_type='manager'
        )

    def test_is_manager_method(self):
        self.assertFalse(self.employee_profile.is_manager())
        self.assertTrue(self.manager_profile.is_manager())

    def test_string_representation(self):
        self.assertEqual(str(self.employee_profile), "testuser - employee")
        self.assertEqual(str(self.manager_profile), "manager - manager")


class PasswordResetTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.password_reset_url = reverse('password_reset')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )

    def test_password_reset_view_GET(self):
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userauth/password_reset.html')

   


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            message="Test notification",
            is_read=False
        )

    def test_mark_as_read(self):
        self.assertFalse(self.notification.is_read)
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)
