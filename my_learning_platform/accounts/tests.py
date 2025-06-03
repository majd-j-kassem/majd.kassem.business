from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

# Import your models from the same app
from .models import (
    CustomUser, Profile, CourseCategory, CourseLevel,
    TeacherCourse, EnrolledCourse, AllowedCard, ContactMessage
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

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpassword'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.user_type, 'admin') # Should be admin if is_staff and is_superuser are true, or explicitly set


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

    def test_profile_creation(self):
        self.assertIsNotNone(self.profile_student)
        self.assertEqual(self.profile_student.user, self.user_student)
        self.assertFalse(self.profile_student.is_teacher_application_pending)
        self.assertFalse(self.profile_student.is_teacher_approved)
        self.assertEqual(self.profile_student.commission_percentage, Decimal('0.00'))

    def test_teacher_application_flow(self):
        profile = self.profile_teacher
        profile.is_teacher_application_pending = True
        profile.full_name_en = "John Doe"
        profile.phone_number = "1234567890"
        profile.save()

        self.assertTrue(profile.is_teacher_application_pending)
        self.assertEqual(profile.full_name_en, "John Doe")

        # Test approval by admin
        profile.is_teacher_application_pending = False
        profile.is_teacher_approved = True
        profile.approved_by = self.user_admin
        profile.approval_date = datetime.now()
        profile.save()

        self.assertFalse(profile.is_teacher_application_pending)
        self.assertTrue(profile.is_teacher_approved)
        self.assertEqual(profile.approved_by, self.user_admin)
        self.assertIsNotNone(profile.approval_date)

        # Test rejection by admin
        profile.is_teacher_approved = False
        profile.rejected_by = self.user_admin
        profile.rejection_date = datetime.now()
        profile.rejection_reason = "Insufficient qualifications"
        profile.save()

        self.assertFalse(profile.is_teacher_approved)
        self.assertEqual(profile.rejected_by, self.user_admin)
        self.assertIsNotNone(profile.rejection_date)
        self.assertEqual(profile.rejection_reason, "Insufficient qualifications")

    def test_commission_percentage(self):
        profile = self.profile_teacher
        profile.commission_percentage = Decimal('10.50')
        profile.save()
        self.assertEqual(profile.commission_percentage, Decimal('10.50'))

        profile.commission_percentage = Decimal('99.99') # Test high but valid
        profile.save()
        self.assertEqual(profile.commission_percentage, Decimal('99.99'))

        # Test invalid commission (e.g., negative or too high, though models.DecimalField handles max_digits/decimal_places)
        # Note: DecimalField does not have built-in min/max value validators like IntegerField
        # You would typically add a custom validator for range if needed beyond max_digits/decimal_places
        # For simplicity, we'll assume it's valid within the schema constraints for now.


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

    def test_create_teacher_course(self):
        course = TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            title="Advanced Python",
            description="Learn advanced Python concepts.",
            price=Decimal('199.99'),
            language='en',
            status='draft',
            video_trailer_url="https://example.com/trailer.mp4"
        )
        course.categories.add(self.category)
        course.level = self.level
        course.save() # Save after adding ManyToMany and ForeignKey

        self.assertEqual(course.title, "Advanced Python")
        self.assertEqual(course.teacher_profile, self.teacher_profile)
        self.assertEqual(course.price, Decimal('199.99'))
        self.assertEqual(course.language, 'en')
        self.assertEqual(course.status, 'draft')
        self.assertTrue(self.category in course.categories.all())
        self.assertEqual(course.level, self.level)
        self.assertFalse(course.featured)
        self.assertIsNotNone(course.created_at)
        self.assertIsNotNone(course.updated_at)
        self.assertEqual(str(course), "Advanced Python (English) by teacheruser")

    def test_course_status_workflow(self):
        course = TeacherCourse.objects.create(
            teacher_profile=self.teacher_profile,
            title="Data Science Basics",
            description="Intro to Data Science.",
            price=Decimal('99.00'),
            language='en',
            status='draft'
        )
        self.assertEqual(course.status, 'draft')

        course.status = 'pending'
        course.save()
        self.assertEqual(course.status, 'pending')

        course.status = 'published'
        course.save()
        self.assertEqual(course.status, 'published')

        course.status = 'rejected'
        course.save()
        self.assertEqual(course.status, 'rejected')

    def test_price_validation(self):
        # Test minimum price validator
        with self.assertRaises(ValidationError):
            course = TeacherCourse(
                teacher_profile=self.teacher_profile,
                title="Invalid Price Course",
                description="Test for price less than 0.",
                price=Decimal('-0.01'), # Invalid price
                language='en',
                status='draft'
            )
            course.full_clean() # Triggers model field validators

        # Test valid zero price
        course_zero_price = TeacherCourse(
            teacher_profile=self.teacher_profile,
            title="Free Course",
            description="Test for zero price.",
            price=Decimal('0.00'),
            language='en',
            status='draft'
        )
        course_zero_price.full_clean() # Should not raise ValidationError
        self.assertEqual(course_zero_price.price, Decimal('0.00'))


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

    def test_enroll_student_in_course(self):
        enrollment = EnrolledCourse.objects.create(
            student=self.student_profile,
            course=self.course,
            fee_paid=self.course.price
        )
        self.assertEqual(enrollment.student, self.student_profile)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.fee_paid, Decimal('50.00'))
        self.assertIsNotNone(enrollment.enrolled_at)
        self.assertEqual(str(enrollment), f"{self.student_user.username} enrolled in {self.course.title}")

    def test_unique_enrollment(self):
        EnrolledCourse.objects.create(
            student=self.student_profile,
            course=self.course,
            fee_paid=self.course.price
        )
        # Attempt to enroll the same student in the same course again
        with self.assertRaises(IntegrityError):
            EnrolledCourse.objects.create(
                student=self.student_profile,
                course=self.course,
                fee_paid=self.course.price
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