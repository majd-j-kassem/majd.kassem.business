# auth_system/accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime
from decimal import Decimal # <--- IMPORTANT: Ensure this import is present!

# --- CustomUser Model ---
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')

    def __str__(self):
        return self.username

# --- Profile Model ---
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')

    profile_picture = models.ImageField(
        upload_to='images/profiles/',
        default='images/profiles/default.jpg',
        blank=True,
        null=True,
    )
    bio = models.TextField(max_length=500, blank=True, null=True)
    full_name_en = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Full Name (English)"
    )
    full_name_ar = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Full Name (Arabic)"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Phone Number"
    )

    experience_years = models.IntegerField(
        verbose_name="Years of Experience",
        default=0,
        blank=True,
        null=True,
        help_text="Number of years of teaching experience."
    )
    university = models.CharField(
        max_length=255,
        verbose_name="University Attended",
        blank=True,
        null=True,
        help_text="Name of the university you graduated from."
    )
    graduation_year = models.IntegerField(
        verbose_name="Graduation Year",
        blank=True,
        null=True,
        help_text="Year of your graduation."
    )
    major = models.CharField(
        max_length=255,
        verbose_name="Major/Specialization",
        blank=True,
        null=True,
        help_text="Your primary field of study."
    )

    is_teacher_application_pending = models.BooleanField(
        default=False,
        help_text="Is the teacher application awaiting admin approval?"
    )
    is_teacher_approved = models.BooleanField(
        default=False,
        help_text="Has the teacher application been approved by an admin?"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_teacher_applications',
        help_text="Admin who approved this teacher application."
    )
    approval_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Date and time when the application was approved."
    )
    rejected_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='rejected_teacher_applications',
        help_text="Admin who rejected this teacher application."
    )
    rejection_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Date and time when the application was rejected."
    )
    rejection_reason = models.TextField(
        null=True, blank=True,
        help_text="Reason for rejection, if applicable."
    )
    commission_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'), # Corrected default to Decimal
        help_text="Commission percentage (e.g., 5.00 for 5%) deducted from course earnings."
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.get_or_create(user=instance)


class CourseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Course Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

class CourseLevel(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Course Levels"
        ordering = ['name']

    def __str__(self):
        return self.name

class TeacherCourse(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    )
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('es', 'Spanish'),
    )
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en', # It's good practice to have a default
        verbose_name="Language of Instruction"
    )
    teacher_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Teacher Profile"
    )
    title = models.CharField(max_length=255, verbose_name="Course Title")
    description = models.TextField(verbose_name="Course Description")
    course_picture = models.ImageField(
        upload_to='course_thumbnails/',
        default='course_thumbnails/default_course.png',
        blank=True,
        null=True
    )
    video_trailer_url = models.URLField(max_length=200, blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Course Price",
        validators=[MinValueValidator(Decimal('0.00'))] # Corrected validator to use Decimal
    )
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='en',
        verbose_name="Instruction Language"
    )
    categories = models.ManyToManyField(
        CourseCategory,
        related_name='courses',
        verbose_name="Categories"
    )
    level = models.ForeignKey(
        CourseLevel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="Level"
    )
    featured = models.BooleanField(
        default=False,
        help_text="Check to mark this course as featured on the homepage."
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current publication status of the course."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Teacher Course"
        verbose_name_plural = "Teacher Courses"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_language_display()}) by {self.teacher_profile.user.username}"


# --- EnrolledCourse Model ---
class EnrolledCourse(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(TeacherCourse, on_delete=models.CASCADE, related_name='enrolled_students')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    fee_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00') # Corrected default to Decimal
    )

    class Meta:
        unique_together = ('student', 'course')
        verbose_name = "Enrolled Course"
        verbose_name_plural = "Enrolled Courses"
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"

# --- AllowedCard Model ---
class AllowedCard(models.Model):
    card_number = models.CharField(max_length=255, unique=True, help_text="The card number.")
    expiry_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Expiry month (1-12)"
    )
    expiry_year = models.IntegerField(
        validators=[
            MinValueValidator(datetime.now().year),
            MaxValueValidator(datetime.now().year + 10)
        ],
        help_text="Expiry year (e.g., 2025)"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Allowed Card"
        verbose_name_plural = "Allowed Cards"
        unique_together = ('card_number', 'expiry_month', 'expiry_year')

    def __str__(self):
        return f"Card ending in {self.card_number[-4:]} (Exp: {self.expiry_month:02d}/{self.expiry_year})"
    
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"

    def __str__(self):
        return f"Message from {self.name} ({self.email})"