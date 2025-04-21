from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core import mail
from django.conf import settings
import pytz
import datetime
from .models import UserProfile, PendingRegistration
from notifications.models import Notification
from tenant_manager.models import Tenant
from unittest.mock import patch, Mock
from tenant_manager.middleware import TenantMiddleware

class TenantTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Create a test user first
        self.owner = User.objects.create_user(
            username='testowner',
            email='owner@example.com',
            password='TestPassword123'
        )
        # Create a test tenant with the owner
        self.tenant = Tenant.objects.create(
            name='test_tenant',
            domain_url='test.localhost',
            schema_name='test_schema',
            owner=self.owner
        )
        # Set up the test client with the tenant domain
        self.client = Client(HTTP_HOST='test.localhost')
        # Disable CSRF checks for testing
        self.client.handler.enforce_csrf_checks = False

    def setup_tenant_request(self, request):
        request.tenant = self.tenant
        request.META['HTTP_HOST'] = 'test.localhost'
        return request

class UserRegistrationTest(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.register_url = reverse('register', kwargs={'tenant_url': 'test'})
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
            'tenant_url': 'test'
        }
        # Set up AJAX headers
        self.ajax_headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

    def test_registration_success(self):
        response = self.client.post(self.register_url, self.valid_data, **self.ajax_headers)
        self.assertEqual(response.status_code, 200)  # AJAX returns 200 with JSON
        
        # Check if user was created (first manager)
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.user_type, 'manager')

    def test_registration_invalid_data(self):
        # Test with invalid data (missing password2)
        invalid_data = self.valid_data.copy()
        del invalid_data['password2']
        response = self.client.post(self.register_url, invalid_data, **self.ajax_headers)
        self.assertEqual(response.status_code, 200)  # AJAX returns 200 with error JSON
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_user_registration_existing_username(self):
        # Create a user first
        User.objects.create_user(username='testuser', email='existing@example.com', password='TestPassword123')
       
        response = self.client.post(self.register_url, self.valid_data, **self.ajax_headers)
        self.assertEqual(response.status_code, 200)  # AJAX returns 200 with error JSON
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("user already exists" in str(message).lower() for message in messages))

    def test_user_registration_existing_email(self):
        # Create a user first
        User.objects.create_user(username='existinguser', email='test@example.com', password='TestPassword123')
       
        response = self.client.post(self.register_url, self.valid_data, **self.ajax_headers)
        self.assertEqual(response.status_code, 200)  # AJAX returns 200 with error JSON
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("email already exists" in str(message).lower() for message in messages))


class UserLoginTest(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.login_url = reverse('login', kwargs={'tenant_url': 'test'})
        self.dashboard_url = reverse('dashboard', kwargs={'tenant_url': 'test'})
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )
        # Create user profile
        UserProfile.objects.create(user=self.user, user_type='employee')
        self.login_data = {
            'username': 'testuser',
            'password': 'TestPassword123'
        }
        self.invalid_login_data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }

    def test_login_view_GET(self):
        request = self.factory.get(self.login_url)
        request = self.setup_tenant_request(request)
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)  # Should redirect to tenant landing page
        self.assertEqual(response.url, '/test/')

    def test_login_valid_credentials(self):
        request = self.factory.post(self.login_url, self.login_data)
        request = self.setup_tenant_request(request)
        response = self.client.post(self.login_url, self.login_data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful login
        self.assertEqual(response.url, self.dashboard_url)
        # Check that UserProfile exists
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_login_invalid_credentials(self):
        request = self.factory.post(self.login_url, self.invalid_login_data)
        request = self.setup_tenant_request(request)
        response = self.client.post(self.login_url, self.invalid_login_data)
        self.assertEqual(response.status_code, 302)  # Should redirect to tenant landing page
        self.assertEqual(response.url, '/test/')
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("username or password does not match" in str(message).lower() for message in messages))


class UserLogoutTest(TenantTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.logout_url = reverse('logout', kwargs={'tenant_url': 'test'})
        self.login_url = reverse('login', kwargs={'tenant_url': 'test'})
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123'
        )
        # Create user profile
        UserProfile.objects.create(user=self.user, user_type='employee')

    def test_logout_view(self):
        request = self.factory.get(self.logout_url)
        request = self.setup_tenant_request(request)
        # Login first
        self.client.login(username='testuser', password='TestPassword123')
       
        # Then logout
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect after logout
        self.assertEqual(response.url, '/test/')  # Should redirect to tenant landing page
       
        # Verify user is logged out by trying to access a protected page
        dashboard_url = reverse('dashboard', kwargs={'tenant_url': 'test'})
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)  # Redirects to login




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



