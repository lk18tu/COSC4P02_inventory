from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

# Create your tests here.

class UserauthTests(TestCase):

	def testSetup(self): #setup test client browser
	
		self.testuser = User.objects.create_user( #create test user credentials for login tests
		username='testtest2',
		password='testpass2',
		email='test2@test2.com'
		)

		self.client = Client(); #setup test browser and urls

		self.login_url = reverse('login')
		self.register_url = reverse('register')
		self.dashboard_url = reverse('dashboard')
		
	def test_Registration(self): #test successful registration

	response = self.client.post(self.register_url, {
	'username' : 'testtest3', #make sure user is not already in database
	'email' : 'testtest3@test3.com',
	'password' : 'testpass3',
	'confirm_password' : 'testpass3' })

	self.assertRedirects(response, self.login_url) # redirect to login page after successful registration
	self.assertTrue(User.objects.filter(username='testtest3').exists()) # check that user is existing in database

	def test_login(self): #test login succesful 

	response = self.client.post(self.login_url, {
	
	'username' : 'testtest2', 
	'password' : 'testpass2' })

	self.assertRedirects(response, self.dashboard_url) #redirects to dashboard upon successful login

	def test_login_fail(self): #test login fail

	response = self.client.post(self.login_url, {
	
	'username' : 'wrongUserName',
	'password' : 'wrongPass' })
	
	reqtest = response.wsgi_request

	self.assertEqual(response.status_code, 200) #Http request successful
	self.assertFalse(reqtest.user.is_authenticated) #assert user is not authenticated



