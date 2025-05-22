# auth_system/accounts/models.py (or wherever your main models.py is)

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime # Use datetime module for current year check

# --- CustomUser Model ---
class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('admin', 'Admin'),
    )
    # The 'user_type' field was duplicated. Keeping only one.
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')

    # The 'email' field is already inherited from AbstractUser and is unique by default in Django 3.0+

    def __str__(self):
        return self.username

# --- Profile Model ---
class Profile(models.Model):
    # OneToOneField to CustomUser is correct
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile') # Added related_name for clarity

    # --- Basic Profile Information ---
    profile_picture = models.ImageField(
        upload_to='images/profiles/', # Good path
        default='images/profiles/default.jpg', # Good default image
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

    # --- Teacher Professional Details (These fields apply only if user.user_type is 'teacher') ---
    experience_years = models.IntegerField(
        verbose_name="Years of Experience",
        default=0, # Default for students too, or consider null=True
        blank=True,
        null=True, # Allow null for students
        help_text="Number of years of teaching experience."
    )
    university = models.CharField(
        max_length=255,
        verbose_name="University Attended",
        blank=True,
        null=True, # Allow null for students
        help_text="Name of the university you graduated from."
    )
    graduation_year = models.IntegerField(
        verbose_name="Graduation Year",
        blank=True,
        null=True, # Allow null for students
        help_text="Year of your graduation."
    )
    major = models.CharField(
        max_length=255,
        verbose_name="Major/Specialization",
        blank=True,
        null=True, # Allow null for students
        help_text="Your primary field of study."
    )

    # --- Teacher Application Status ---
    # These fields relate to the approval workflow for teachers
    is_teacher_application_pending = models.BooleanField(
        default=False, # Default to False. It becomes True when a user starts a teacher application.
        help_text="Is the teacher application awaiting admin approval?"
    )
    is_teacher_approved = models.BooleanField(
        default=False, # Not approved until admin acts
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

    class Meta:
        verbose_name = "User Profile" # More generic verbose name
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.username}'s Profile"


# --- Signals to automatically create/save Profile when CustomUser is created/saved ---

@receiver(post_save, sender=CustomUser)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Create a new Profile only if one doesn't already exist for this user
        Profile.objects.get_or_create(user=instance)
    else:
        # Try to save the profile. If it doesn't exist, it will be created by get_or_create
        # when the user is first created (due to the `if created` block).
        # This prevents an error if instance.profile somehow doesn't exist on subsequent saves.
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            # Fallback for very rare cases where a user exists but no profile was created
            # This should ideally not be hit with the `get_or_create` above, but it's safer.
            Profile.objects.get_or_create(user=instance)


# --- Course Offering Models (Moved to a separate 'courses' app for better organization if not already done) ---

# Suggestion: It's highly recommended to move these models to a dedicated 'courses' app
# (e.g., courses/models.py) and import them into this accounts/models.py if needed,
# or define them there and reference them.
# For now, I'm keeping them here as provided, but noting the best practice.

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
        ('pending', 'Pending Review'), # Course submitted by teacher, awaiting admin approval
        ('approved', 'Approved'),     # Admin approved, but not yet publicly listed
        ('rejected', 'Rejected'),     # Admin rejected
        ('published', 'Published'),   # Live and visible to students
        ('archived', 'Archived'),     # No longer active/visible
    )
    # Define LANGUAGE_CHOICES for the 'language' field
    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('es', 'Spanish'),
        # Add more languages as needed
    )

    teacher_profile = models.ForeignKey(
        Profile, # Link to the Profile model
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Teacher Profile"
    )
    title = models.CharField(max_length=255, verbose_name="Course Title")
    description = models.TextField(verbose_name="Course Description")
    course_picture = models.ImageField(
        upload_to='course_thumbnails/',
        default='course_thumbnails/default_course.png', # Provide a default for courses too
        blank=True,
        null=True
    )
    video_trailer_url = models.URLField(max_length=200, blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Course Price",
        validators=[MinValueValidator(0.00)] # Price cannot be negative
    )
    language = models.CharField(
        max_length=2, # Changed to 2 for ISO 639-1 codes (e.g., 'en', 'ar')
        choices=LANGUAGE_CHOICES,
        default='en',
        verbose_name="Instruction Language"
    )
    categories = models.ManyToManyField(
        CourseCategory, # Link to CourseCategory model
        related_name='courses',
        verbose_name="Categories"
    )
    level = models.ForeignKey(
        CourseLevel, # Link to CourseLevel model
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
        verbose_name = "Teacher Course" # Changed from "Course" for clarity
        verbose_name_plural = "Teacher Courses"
        ordering = ['-created_at'] # Order newest first by default

    def __str__(self):
        # Using get_language_display for human-readable language
        return f"{self.title} ({self.get_language_display()}) by {self.teacher_profile.user.username}"


# --- EnrolledCourse Model ---
class EnrolledCourse(models.Model):
    # ForeignKeys to Profile and TeacherCourse
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(TeacherCourse, on_delete=models.CASCADE, related_name='enrolled_students')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course') # Ensures a student can enroll in a course only once
        verbose_name = "Enrolled Course"
        verbose_name_plural = "Enrolled Courses"
        ordering = ['-enrolled_at'] # Default ordering for enrolled courses

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"

# --- AllowedCard Model ---
class AllowedCard(models.Model):
    """
    Model to store card details that are considered 'valid' for payment.
    For a real system, card numbers would be encrypted and never stored directly.
    Expiry month and year are stored as integers.
    """
    # Use a specific max_length (e.g., 16-19 for card numbers) or consider encrypting.
    # Storing raw card numbers directly in a database is a major security risk (PCI DSS compliance).
    # For a personal project, it might be acceptable for dummy data, but be aware for production.
    card_number = models.CharField(max_length=255, unique=True, help_text="The card number.") # Still max_length 255 if needed for encryption/token
    expiry_month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Expiry month (1-12)"
    )
    expiry_year = models.IntegerField(
        validators=[
            MinValueValidator(datetime.now().year), # Current year as minimum
            MaxValueValidator(datetime.now().year + 10) # Example: max 10 years in future
        ],
        help_text="Expiry year (e.g., 2025)"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Allowed Card"
        verbose_name_plural = "Allowed Cards"
        # Unique constraint for card number + expiry date is good for preventing exact duplicates
        unique_together = ('card_number', 'expiry_month', 'expiry_year')

    def __str__(self):
        # Mask the card number for display
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
