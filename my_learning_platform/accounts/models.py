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