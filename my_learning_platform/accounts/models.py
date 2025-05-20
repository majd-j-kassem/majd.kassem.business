# auth_system/accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student',
    )
    # The 'email' field is already inherited from AbstractUser

    def __str__(self):
        return self.username


class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
        # --- New Fields for Teacher Professional Details ---
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
    # Existing fields
    profile_picture = models.ImageField(
        upload_to='images/profiles/',
        default='images/profiles/default.jpg',
        blank=True,
        null=True,
    )
    bio = models.TextField(max_length=500, blank=True, null=True)

    # New fields for basic teacher information
    full_name_en = models.CharField(
        max_length=255,
        blank=True, # Allows the field to be blank in the form
        null=True,  # Allows the field to be NULL in the database
        verbose_name="Full Name (English)" # User-friendly name for admin/forms
    )
    full_name_ar = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Full Name (Arabic)"
    )
    phone_number = models.CharField(
        max_length=20, # Adjust max_length based on expected phone number formats
        blank=True,
        null=True,
        verbose_name="Phone Number"
    )
     # --- New Fields for Teacher Application Status ---
    is_teacher_application_pending = models.BooleanField(
        default=True, # New applications are pending by default
        help_text="Is the teacher application awaiting admin approval?"
    )
    is_teacher_approved = models.BooleanField(
        default=False, # Not approved until admin acts
        help_text="Has the teacher application been approved by an admin?"
    )
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL, # If the approving admin is deleted, don't delete the approval record
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
        on_delete=models.SET_NULL, # If the rejecting admin is deleted, don't delete the rejection record
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
    # ... (rest of your Profile model fields) ...
    is_teacher_application_pending = models.BooleanField(default=False)
    is_teacher_approved = models.BooleanField(default=False)
    # (Optional: If you track who approved/rejected and when)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_teachers')
    approval_date = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_teachers')
    rejection_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.user.username}'s Profile"
    def __str__(self):
        return f'{self.user.username} Profile'


# --- Signals to automatically create/save Profile when User is created/saved ---

# Signal receiver function to create a Profile whenever a new User is created
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Signal receiver function to save the Profile whenever the User is saved
@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    # Ensure the profile exists before attempting to save it.
    # This handles cases where a CustomUser might exist without an associated Profile,
    # ensuring that instance.profile is always available.
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    instance.profile.save()

# auth_system/accounts/models.py

# ... (Keep all your existing imports and models like CustomUser and Profile) ...
# Ensure CustomUser and Profile are imported correctly.
# Example: from .models import CustomUser # if CustomUser is in this same file

# --- New Models for Course Offerings ---

class CourseCategory(models.Model):
    """
    Represents categories for courses (e.g., 'Art', 'Computer Science').
    Managed by admin.
    """
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Course Categories"
        ordering = ['name'] # Order alphabetically in admin

    def __str__(self):
        return self.name

class CourseLevel(models.Model):
    """
    Represents difficulty levels for courses (e.g., 'Beginner', 'Intermediate').
    Managed by admin.
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "Course Levels"
        ordering = ['name'] # Order alphabetically in admin

    def __str__(self):
        return self.name

class TeacherCourse(models.Model):
    """
    Represents a specific course offered by a teacher.
    Linked to the teacher's Profile.
    """
    teacher_profile = models.ForeignKey(
        'Profile',  # Use string literal if Profile is defined later in the file, or import it
        on_delete=models.CASCADE,
        related_name='offered_courses',
        verbose_name="Teacher Profile"
    )
    categories = models.ManyToManyField(
        CourseCategory,
        related_name='courses_offered',
        verbose_name="Categories"
    )
    level = models.ForeignKey(
        CourseLevel,
        on_delete=models.SET_NULL, # If a level is deleted, courses remain but level becomes null
        null=True,
        blank=True,
        related_name='courses_at_level',
        verbose_name="Level"
    )
    title = models.CharField(max_length=255, verbose_name="Course Title")
    description = models.TextField(verbose_name="Course Description")
    price = models.DecimalField(
        max_digits=8,          # Allows numbers up to 999999.99
        decimal_places=2,      # Two decimal places for currency
        verbose_name="Course Price"
    )
    language = models.CharField(
        max_length=100,
        verbose_name="Instruction Language",
        help_text="e.g., English, Arabic, French"
    )

    class Meta:
        verbose_name_plural = "Teacher Courses"
        ordering = ['title'] # Order by title by default

    def __str__(self):
        return f"{self.title} ({self.language}) by {self.teacher_profile.user.username}"