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
        self.assertEqual(form.cleaned_data['username'], 'testuser')
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
        
        
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

from accounts.models import (
    CustomUser, CourseCategory, CourseLevel,
    AllowedCard, ContactMessage, TeacherCourse, EnrolledCourse
)

# Get the CustomUser model for consistency
User = get_user_model()

class CustomUserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='strongpassword'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('strongpassword'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.user_type, 'student') # Default user type

class ProfileModelTest(TestCase):
    def setUp(self):
        self.user_student = User.objects.create_user(
            username='student1', email='student1@example.com', password='password123', user_type='student'
        )
        self.user_teacher = User.objects.create_user(
            username='teacher1', email='teacher1@example.com', password='password123', user_type='teacher'
        )
        self.user_admin = User.objects.create_superuser(
            username='admin1', email='admin1@example.com', password='adminpassword'
        )
        # Profile is created automatically by post_save signal or get_or_create in your setup
        self.profile_student = Profile.objects.get(user=self.user_student)
        self.profile_teacher = Profile.objects.get(user=self.user_teacher)
        self.profile_admin = Profile.objects.get(user=self.user_admin)


class CourseCategoryModelTest(TestCase):
    def test_create_category(self):
        category = CourseCategory.objects.create(name="Mathematics")
        self.assertEqual(category.name, "Mathematics")
        self.assertEqual(str(category), "Mathematics")

    def test_unique_category_name(self):
        CourseCategory.objects.create(name="Science")
        with self.assertRaises(IntegrityError):
            CourseCategory.objects.create(name="Science")


class CourseLevelModelTest(TestCase):
    def test_create_level(self):
        level = CourseLevel.objects.create(name="Beginner")
        self.assertEqual(level.name, "Beginner")
        self.assertEqual(str(level), "Beginner")

    def test_unique_level_name(self):
        CourseLevel.objects.create(name="Intermediate")
        with self.assertRaises(IntegrityError):
            CourseLevel.objects.create(name="Intermediate")


class TeacherCourseModelTest(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacheruser', email='teacher@example.com', password='password123', user_type='teacher'
        )
        self.teacher_profile = Profile.objects.get(user=self.teacher_user)
        self.teacher_profile.is_teacher_approved = True # Teacher must be approved to create courses usually
        self.teacher_profile.save()

        self.category = CourseCategory.objects.create(name="Programming")
        self.level = CourseLevel.objects.create(name="Advanced")


class EnrolledCourseModelTest(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='studentuser', email='student@example.com', password='password123', user_type='student'
        )
        self.student_profile = Profile.objects.get(user=self.student_user)

        self.teacher_user = User.objects.create_user(
            username='teacheruser', email='teacher@example.com', password='password123', user_type='teacher'
        )
        self.teacher_profile = Profile.objects.get(user=self.teacher_user)
        self.teacher_profile.is_teacher_approved = True
        self.teacher_profile.save()

        self.course = TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            title="Web Development Basics",
            description="Learn HTML, CSS, JS.",
            price=Decimal('50.00'),
            language='en',
            status='published'
        )

  
  
class AllowedCardModelTest(TestCase):
    def test_create_allowed_card(self):
        current_year = datetime.now().year
        card = AllowedCard.objects.create(
            card_number='1234567890123456',
            expiry_month=12,
            expiry_year=current_year + 1
        )
        self.assertEqual(card.card_number, '1234567890123456')
        self.assertEqual(card.expiry_month, 12)
        self.assertEqual(card.expiry_year, current_year + 1)
        self.assertIsNotNone(card.added_at)
        self.assertEqual(str(card), f"Card ending in 3456 (Exp: 12/{current_year + 1})")

    def test_card_number_uniqueness(self):
        current_year = datetime.now().year
        AllowedCard.objects.create(
            card_number='1111222233334444',
            expiry_month=10,
            expiry_year=current_year + 2
        )
        with self.assertRaises(IntegrityError):
            AllowedCard.objects.create(
                card_number='1111222233334444', # Duplicate card number
                expiry_month=11,
                expiry_year=current_year + 3
            )

    def test_expiry_month_validation(self):
        current_year = datetime.now().year
        with self.assertRaises(ValidationError):
            card = AllowedCard(
                card_number='9876543210987654',
                expiry_month=0, # Invalid month
                expiry_year=current_year + 1
            )
            card.full_clean() # Triggers validators

        with self.assertRaises(ValidationError):
            card = AllowedCard(
                card_number='9876543210987654',
                expiry_month=13, # Invalid month
                expiry_year=current_year + 1
            )
            card.full_clean()

    def test_expiry_year_validation(self):
        current_year = datetime.now().year
        with self.assertRaises(ValidationError):
            card = AllowedCard(
                card_number='1234123412341234',
                expiry_month=1,
                expiry_year=current_year - 1 # Invalid year (past)
            )
            card.full_clean()

        with self.assertRaises(ValidationError):
            card = AllowedCard(
                card_number='1234123412341234',
                expiry_month=1,
                expiry_year=current_year + 11 # Invalid year (too far future)
            )
            card.full_clean()

    def test_unique_together(self):
        current_year = datetime.now().year
        AllowedCard.objects.create(
            card_number='5555666677778888',
            expiry_month=5,
            expiry_year=current_year + 2
        )
        with self.assertRaises(IntegrityError):
            AllowedCard.objects.create(
                card_number='5555666677778888', # Same card_number, month, year
                expiry_month=5,
                expiry_year=current_year + 2
            )

class ContactMessageModelTest(TestCase):
    def test_create_contact_message(self):
        message = ContactMessage.objects.create(
            name="Jane Doe",
            email="jane@example.com",
            phone_number="9876543210",
            message="This is a test message."
        )
        self.assertEqual(message.name, "Jane Doe")
        self.assertEqual(message.email, "jane@example.com")
        self.assertEqual(message.phone_number, "9876543210")
        self.assertEqual(message.message, "This is a test message.")
        self.assertIsNotNone(message.submitted_at)
        self.assertEqual(str(message), "Message from Jane Doe (jane@example.com)")

    def test_message_without_phone(self):
        message = ContactMessage.objects.create(
            name="John Smith",
            email="john@example.com",
            message="Another test message."
        )
        self.assertEqual(message.name, "John Smith")
        self.assertEqual(message.email, "john@example.com")
        self.assertIsNone(message.phone_number) # Should be None because blank=True, null=True
        self.assertEqual(message.message, "Another test message.")

