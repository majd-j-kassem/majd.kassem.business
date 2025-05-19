from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token  # Import Token if you're using TokenAuthentication

User = get_user_model()

class UserRegistrationIntegrationTests(APITestCase):
    """
    Integration tests for the user registration API endpoint.
    """

    def test_successful_user_registration(self):
        """
        Test the successful registration of a new user.
        """
        url = reverse('api_register')
        data = {
            'username': 'newintegrationuser',
            'email': 'newintegration@example.com',
            'password': 'integrationpassword123',
            'password2': 'integrationpassword123',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the user exists in the database
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(username='newintegrationuser')
        self.assertEqual(user.email, 'newintegration@example.com')
        self.assertTrue(user.check_password('integrationpassword123'))

    def test_registration_with_existing_email(self):
        """
        Test registration attempt with an already existing email.
        """
        User.objects.create_user(username='existing', email='existing@example.com', password='password')
        url = reverse('api_register')
        data = {
            'username': 'anotheruser',
            'email': 'existing@example.com',
            'password': 'somepassword',
            'password2': 'somepassword',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_registration_with_password_mismatch(self):
        """
        Test registration attempt with mismatched passwords.
        """
        url = reverse('api_register')
        data = {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'password1',
            'password2': 'password2',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class UserLoginIntegrationTests(APITestCase):
    """
    Integration tests for the user login API endpoint.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testlogin', email='testlogin@example.com', password='loginpassword')
        self.login_url = reverse('api_login')

    def test_successful_user_login(self):
        """
        Test successful login with correct credentials.
        """
        data = {
            'username_or_email': 'testlogin',
            'password': 'loginpassword',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)  # Check for the token in the response

    def test_successful_user_login_with_email(self):
        """
        Test successful login with correct credentials using email.
        """
        data = {
            'username_or_email': 'testlogin@example.com',
            'password': 'loginpassword',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)  # Check for the token

    def test_login_with_incorrect_password(self):
        """
        Test login attempt with an incorrect password.
        """
        data = {
            'username_or_email': 'testlogin',
            'password': 'wrongpassword',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_with_nonexistent_user(self):
        """
        Test login attempt with a nonexistent username/email.
        """
        data = {
            'username_or_email': 'nonexistentuser',
            'password': 'anypassword',
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_with_missing_fields(self):
        """
        Test login attempt with missing required fields.
        """
        response = self.client.post(self.login_url, {'username_or_email': 'testlogin'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        response = self.client.post(self.login_url, {'password': 'loginpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username_or_email', response.data)


class UserLogoutIntegrationTests(APITestCase):
    """
    Integration tests for the user logout API endpoint.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.token = Token.objects.create(user=self.user)  # Create a token for the user
        self.logout_url = reverse('api_logout')

    def test_successful_user_logout(self):
        """
        Test successful logout.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)  # Authenticate the client
        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Successfully logged out.')
        self.assertFalse(Token.objects.filter(key=self.token.key).exists())


    def test_logout_without_authentication(self):
        """
        Test logout attempt without authentication.
        """
        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Or 403, depending on your permission class


class UserDetailIntegrationTests(APITestCase):
    """
    Integration tests for the user detail API endpoint.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        self.user_detail_url = reverse('api_user_detail')

    def test_get_user_details(self):
        """
        Test retrieving user details.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        response = self.client.get(self.user_detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_get_user_details_unauthenticated(self):
        """
        Test retrieving user details without authentication.
        """
        response = self.client.get(self.user_detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
