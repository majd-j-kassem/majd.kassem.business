from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import Profile, CourseCategory, CourseLevel, TeacherCourse

User = get_user_model()

class UserFlowsIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')
        self.profile_update_url = reverse('accounts:profile_update') # Assuming this URL name

        # Create an admin user for approval scenarios
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='adminpassword'
        )

    def test_full_user_registration_workflow(self):
        """
        Tests the complete user registration process from GET to successful POST
        and redirection.
        """
        # 1. GET the registration page
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/registration.html')

        # 2. POST valid data to registration
        response = self.client.post(self.register_url, {
            'username': 'newstudent',
            'email': 'student@example.com',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
            'user_type': 'student', # Ensure this matches your form
        })

        # 3. Assert successful registration and redirection
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.login_url)

        # 4. Verify user and profile creation in the database
        self.assertTrue(User.objects.filter(username='newstudent').exists())
        student_user = User.objects.get(username='newstudent')
        self.assertEqual(student_user.email, 'student@example.com')
        self.assertEqual(student_user.user_type, 'student')
        self.assertTrue(Profile.objects.filter(user=student_user).exists())
        self.assertFalse(Profile.objects.get(user=student_user).is_teacher_approved)


    def test_login_logout_workflow(self):
        """
        Tests user login and logout sequence.
        """
        # Create a user to log in
        user = User.objects.create_user(username='testuser', email='test@test.com', password='password123')

        # 1. Attempt to log in with correct credentials
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302) # Should redirect after login
        self.assertTrue(response.wsgi_request.user.is_authenticated) # User should be logged in

        # 2. Attempt to log out
        response = self.client.get(self.logout_url, follow=True) # follow=True to resolve redirect
        self.assertEqual(response.status_code, 200) # Should be OK after redirect
        self.assertFalse(response.wsgi_request.user.is_authenticated) # User should be logged out
        # You might assert a message or specific template for logout success


    def test_teacher_application_and_approval_workflow(self):
        """
        Tests the flow of a student becoming a teacher and admin approval.
        Requires appropriate URLs and views for this process.
        """
        # 1. Create a student user
        student_user = User.objects.create_user(
            username='teacher_applicant', email='applicant@example.com', password='password123', user_type='student'
        )
        profile = Profile.objects.get(user=student_user)
        self.assertFalse(profile.is_teacher_application_pending)
        self.assertFalse(profile.is_teacher_approved)

        # 2. Student logs in
        self.client.login(username='teacher_applicant', password='password123')

        # 3. Student submits teacher application (simulate POST to a profile update form)
        #    Assuming your profile_update_url handles this and updates is_teacher_application_pending
        response = self.client.post(self.profile_update_url, {
            'full_name_en': 'Applicant Name',
            'phone_number': '1122334455',
            'is_teacher_application_pending': True, # Or your form's equivalent field
            # ... include other required profile fields
        })
        self.assertEqual(response.status_code, 302) # Assuming redirect after successful update
        profile.refresh_from_db() # Reload profile to get updated status
        self.assertTrue(profile.is_teacher_application_pending)
        self.assertEqual(profile.user.user_type, 'student') # User type should still be student

        # 4. Admin logs in
        self.client.logout() # Logout student
        self.client.login(username='admin', password='adminpassword')

        # 5. Admin approves the teacher application
        #    This often involves a separate admin view or directly modifying through the Django admin
        #    For this test, we'll simulate a POST to a hypothetical admin approval URL,
        #    or directly update the profile and check. Let's assume a direct update for simplicity,
        #    but ideally you'd test the admin view's POST.
        profile.is_teacher_application_pending = False
        profile.is_teacher_approved = True
        profile.approved_by = self.admin_user
        profile.save()
        profile.user.user_type = 'teacher' # Manually change user type if not handled by a signal/view
        profile.user.save()

        # 6. Verify profile status and user type change
        profile.refresh_from_db()
        self.assertFalse(profile.is_teacher_application_pending)
        self.assertTrue(profile.is_teacher_approved)
        self.assertEqual(profile.user.user_type, 'teacher')
        self.assertEqual(profile.approved_by, self.admin_user)