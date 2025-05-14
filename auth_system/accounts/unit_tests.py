# accounts/tests.py
from django.test import TestCase # You can still use this for simple tests not needing DRF specifics
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

# Import your serializers and models
from .serializers import UserRegisterSerializer, UserLoginSerializer
# If you had custom models, import them here too, e.g., from .models import MyModel
from .api_views import UserDetailAPIView

User = get_user_model()

# --- Unit Tests for Serializers ---

class UserRegisterSerializerTests(APITestCase): # Use APITestCase for tests involving DRF components and DB

    def test_valid_registration_data(self):
        """
        Test that the serializer is valid with correct data.
        """
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'securepassword123',
            'password2': 'securepassword123',
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid()) # Check if validation passes

        # Check that the validated data excludes password2
        validated_data = serializer.validated_data
        #self.assertNotIn('password2', validated_data)
        self.assertEqual(validated_data['username'], 'testuser')
        self.assertEqual(validated_data['email'], 'test@example.com')
        self.assertEqual(validated_data['password'], 'securepassword123') # Password is not hashed yet here

    def test_registration_password_mismatch(self):
        """
        Test that password mismatch raises a validation error.
        """
        data = {
            'username': 'testuser2',
            'email': 'test2@example.com',
            'password': 'securepassword123',
            'password2': 'wrongpassword', # Passwords don't match
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid()) # Validation should fail

        # Check specific error for password mismatch
        self.assertIn('password', serializer.errors)
        self.assertEqual(serializer.errors['password'][0], "Password fields didn't match.")

    def test_registration_email_already_exists(self):
        """
        Test that using an existing email raises a validation error.
        """
        # First, create a user with an email
        User.objects.create_user(username='existinguser', email='exists@example.com', password='password')

        data = {
            'username': 'testuser3',
            'email': 'exists@example.com', # This email already exists
            'password': 'securepassword123',
            'password2': 'securepassword123',
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid()) # Validation should fail

        # Check specific error for email already exists
        self.assertIn('email', serializer.errors)
        self.assertEqual(serializer.errors['email'][0], "This email address is already in use.")

    def test_registration_missing_required_fields(self):
        """
        Test that missing required fields (username, email, password, password2) cause validation errors.
        """
        data = {
            'username': 'incompleteuser',
            'password': 'securepassword123',
            'password2': 'securepassword123',
            # Email is missing
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors) # Check for error on missing email

        data = { # Missing everything
             'username': '', 'email': '', 'password': '', 'password2': ''
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username', serializer.errors)
        self.assertIn('email', serializer.errors)
        self.assertIn('password', serializer.errors)
        self.assertIn('password2', serializer.errors)


    def test_registration_create_user(self):
        """
        Test that the create method correctly creates a user with a hashed password.
        """
        data = {
            'username': 'newlycreateduser',
            'email': 'create@example.com',
            'password': 'securepassword456',
            'password2': 'securepassword456',
        }
        serializer = UserRegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Call the create method
        user = serializer.save() # .save() calls create() or update()

        # Check if the user was created in the database
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newlycreateduser')
        self.assertEqual(user.email, 'create@example.com')

        # Check that the password was correctly set and hashed
        self.assertTrue(user.check_password('securepassword456'))
        self.assertFalse(user.check_password('password456')) # Ensure it's hashed


class UserLoginSerializerTests(APITestCase):

    def test_valid_login_data(self):
        """
        Test that the login serializer is valid with correct data format.
        (Authentication logic is in the view, this only tests data format)
        """
        data = {
            'username_or_email': 'testuser',
            'password': 'anypassword', # Password content doesn't matter for serializer validation
        }
        serializer = UserLoginSerializer(data=data)
        self.assertTrue(serializer.is_valid()) # Should pass because format is correct

        validated_data = serializer.validated_data
        self.assertEqual(validated_data['username_or_email'], 'testuser')
        self.assertEqual(validated_data['password'], 'anypassword')

    def test_login_missing_fields(self):
        """
        Test that missing fields cause validation errors for login serializer.
        """
        data = {
            'username_or_email': 'testuser',
            # Password is missing
        }
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

        data = {
            # Both missing
        }
        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('username_or_email', serializer.errors)
        self.assertIn('password', serializer.errors)

# --- Add more tests here for other components if needed ---

# Example: Testing the get_object method in UserDetailAPIView (partial view unit test)
from rest_framework.test import APIRequestFactory # Useful for testing views directly

class UserDetailAPIViewTests(APITestCase):

    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(username='authuser', email='auth@example.com', password='securepassword')
        self.factory = APIRequestFactory()

    def test_get_object_returns_authenticated_user(self):
        """
        Test that get_object returns the request.user.
        """
        # Simulate an authenticated request
        request = self.factory.get('/api/user/') # The URL doesn't matter for get_object
        request.user = self.user # Manually set the authenticated user on the request

        # Instantiate the view and call get_object
        view = UserDetailAPIView()
        view.request = request # Attach the request to the view instance

        # Check if get_object returns the correct user
        authenticated_user = view.get_object()
        self.assertEqual(authenticated_user, self.user)

    # Note: Testing the full UserDetailAPIView response requires Integration Tests
    # using the test client, which we'll cover later.