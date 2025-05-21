# auth_system/accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('teacher', 'Teacher'),
         ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
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
    
    # --- Teacher Professional Details ---
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

    # Basic teacher information (consolidated)
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
    
    # --- Teacher Application Status (consolidated) ---
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
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_teacher_applications', # Good related_name
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
        related_name='rejected_teacher_applications', # Good related_name
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

    # Consolidated __str__ method
    def __str__(self):
        return f"{self.user.username}'s Profile"


# --- Signals to automatically create/save Profile when User is created/saved ---

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    # Ensure the profile exists before attempting to save it.
    # This handles cases where a CustomUser might exist without an associated Profile,
    # ensuring that instance.profile is always available.
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    instance.profile.save()

# --- New Models for Course Offerings ---

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    course_picture = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    video_trailer_url = models.URLField(max_length=200, blank=True, null=True)

    teacher_profile = models.ForeignKey(
        'Profile',
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name="Teacher Profile"
    )
    categories = models.ManyToManyField(
        'CourseCategory',
        related_name='courses',
        verbose_name="Categories"
    )
    level = models.ForeignKey(
        'CourseLevel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="Level"
    )
    title = models.CharField(max_length=255, verbose_name="Course Title")
    description = models.TextField(verbose_name="Course Description")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Course Price"
    )
    language = models.CharField(
        max_length=100,
        verbose_name="Instruction Language",
        help_text="e.g., English, Arabic, French"
    )

    class Meta:
        verbose_name_plural = "Teacher Courses"
        ordering = ['-created_at']

    # Consolidated __str__ method (more descriptive)
    def __str__(self):
        return f"{self.title} ({self.language}) by {self.teacher_profile.user.username}"
    
class EnrolledCourse(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(TeacherCourse, on_delete=models.CASCADE, related_name='enrolled_students')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course') # Ensures a student can enroll in a course only once
        verbose_name = "Enrolled Course"
        verbose_name_plural = "Enrolled Courses"

    def __str__(self):
        return f"{self.student.user.username} enrolled in {self.course.title}"
