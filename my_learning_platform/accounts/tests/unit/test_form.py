from django.test import TestCase
from accounts.forms import UserRegistrationForm, ProfileForm

from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class UserRegistrationFormTest(TestCase):
    def test_valid_registration_form(self):
        """Test UserRegistrationForm with valid data."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'user_type': 'student',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors) # Assert True, and print errors if not valid

        # Verify cleaned data
        self.assertNotEqual(form.cleaned_data['username'], 'testuser')
        self.assertEqual(form.cleaned_data['email'], 'test@example.com')
        self.assertIn('password', form.cleaned_data) # Password will be hashed/processed by the form
        
    def test_invalid_registration_form_password_mismatch(self):
        """Test UserRegistrationForm with password mismatch."""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Password123!',
            'password2': 'MismatchPassword!', # Mismatch
            'user_type': 'student',
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors) # Check for error on password2 field
        self.assertIn("Passwords don't match.", form.errors['password2'])

