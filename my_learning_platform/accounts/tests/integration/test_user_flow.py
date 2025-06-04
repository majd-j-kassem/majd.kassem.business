from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO

from accounts.models import Profile

from accounts.forms import SignupForm  # Corrected form name

User = get_user_model()

class UserFlowsIntegrationTest(TestCase):
    """
    Integration tests for core user flows: registration, login, and logout.
    """

    def setUp(self):
        """
        Set up common test data and URLs.
        """
        self.client = Client()

        # Define URLs using their 'name' from urls.py
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        
        self.dashboard_url = reverse('dashboard')  
        self.index_url = reverse('index') # Your homepage URL (usually '/')

        # Optional: Create an admin user if any tests need admin login
        # self.admin_user = User.objects.create_superuser(
        #     username='adminuser', email='admin@example.com', password='adminpassword123'
        # )

    def test_full_user_registration_workflow(self):
        """
        Tests the complete user registration process from GET to successful POST,
        and verifies user/profile creation and redirection.
        """
        # 1. GET the signup page
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)

        # Assert specific text from the page content (case-sensitive as seen in your HTML)
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'Create Your Account')
        self.assertContains(response, '<form method="post" enctype="multipart/form-data">')

        # Assert that the form is present in the context
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], SignupForm)

        # Initial user and profile count before POST
        initial_user_count = User.objects.count()
        initial_profile_count = Profile.objects.count()

        # 2. Prepare valid registration data for POST
        new_username = 'testuser123'
        new_email = 'testuser123@example.com'
        new_password = 'securepassword123'

        # Create a dummy image file for profile_picture upload (minimal GIF)
        image_content = BytesIO(b"GIF89a\x01\x00\x01\x00\x00\xff\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")
        profile_pic = SimpleUploadedFile("test_profile.gif", image_content.getvalue(), content_type="image/gif")

        registration_data = {
            'username': new_username,
            'email': new_email,
            'full_name_en': 'John Doe',
            'full_name_ar': 'جون دو',
            # Add 'password1' if your SignupForm explicitly expects it in addition to 'password'
            # Based on your error, it seems your form is expecting 'password1'
            'password': new_password, 
            'password2': new_password, 
            'password1': new_password, # <--- ADD THIS LINE if your form explicitly needs 'password1'
            'profile_picture': profile_pic,
            'bio': 'A new user learning Django integration tests.',
        }

        # 3. POST the registration data
        post_response = self.client.post(self.signup_url, registration_data, follow=True)

        # --- DEBUGGING / ASSERTION FOR SIGNUP REDIRECTION ---
        if post_response.status_code == 200 and 'form' in post_response.context:
            print("\n--- Signup Form Errors (for test_full_user_registration_workflow) ---")
            print(post_response.context['form'].errors)
            print("--------------------------------------------------\n")
        elif post_response.status_code == 200:
             print("\n--- Unexpected 200 response without form context ---")
             print(f"Response URL: {post_response.request['PATH_INFO']}")
             print(f"Response Content (first 200 chars): {post_response.content[:200].decode()}")
             print("--------------------------------------------------\n")

        # Assertions after successful registration (and redirection)
        self.assertRedirects(post_response, self.login_url)
        self.assertEqual(post_response.status_code, 200) 


        # Verify a new user was created in the database
        self.assertEqual(User.objects.count(), initial_user_count + 1)
        created_user = User.objects.filter(username=new_username, email=new_email).first()
        self.assertIsNotNone(created_user)  
        self.assertTrue(created_user.check_password(new_password))


        # Verify the associated profile was created and fields are set (assuming a signal creates it)
        self.assertEqual(Profile.objects.count(), initial_profile_count + 1)
        self.assertTrue(hasattr(created_user, 'profile'))  
        self.assertEqual(created_user.profile.full_name_en, 'John Doe')
        self.assertEqual(created_user.profile.full_name_ar, 'جون دو')
        self.assertEqual(created_user.profile.bio, 'A new user learning Django integration tests.')
        self.assertIsNotNone(created_user.profile.profile_picture)  

        # Ensure the user is NOT logged in automatically after registration (common default behavior)
        self.assertFalse('_auth_user_id' in self.client.session)


    def test_login_logout_workflow(self):
        """
        Tests the user login and logout sequence:
        1. Create a user.
        2. Attempt to login with correct credentials.
        3. Assert successful login, session update, and redirection.
        4. Attempt to logout.
        5. Assert successful logout, session clear, and redirection.
        """
        # 1. Create a test user for login/logout
        username = 'login_test_user'
        password = 'testpassword123'
        user = User.objects.create_user(username=username, email='login@example.com', password=password)
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user) 

        # Initial checks (user not logged in)
        self.assertFalse('_auth_user_id' in self.client.session)

        # --- Phase 1: Login ---
        login_data = {
            'username': username,
            'password': password
        }
        login_response = self.client.post(self.login_url, login_data, follow=True)

        # Assertions after successful login
        self.assertEqual(login_response.status_code, 200)  
        self.assertRedirects(login_response, self.index_url) 
        
        # --- IMPORTANT: CHANGE THIS STRING ---
        # Update this to match the exact text found in the HTML output for your homepage,
        # e.g., 'Welcome to Our Learning Platform!' or 'Welcome to My Portfolio'
        self.assertContains(login_response, 'Welcome to Our Learning Platform!') # Corrected string


        # Verify user is logged in by checking the session
        self.assertTrue('_auth_user_id' in self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

        # --- Phase 2: Logout ---
        logout_response = self.client.get(self.logout_url, follow=True)

        # Assertions after successful logout
        self.assertEqual(logout_response.status_code, 200)  
        self.assertRedirects(logout_response, self.index_url)
        
        # --- IMPORTANT: CHANGE THIS STRING ---
        # Update this to match the exact text found in the HTML output for your homepage after logout.
        self.assertContains(logout_response, 'Welcome to Our Learning Platform!') # Corrected string

        # Verify user is logged out by checking the session
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertIsNone(self.client.session.get('_auth_user_id'))