# auth_system/accounts/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save # Import signal
from django.dispatch import receiver # Import receiver

# Get the currently active User model
User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # ImageField requires Pillow to be installed: pip install Pillow
    # 'images/profiles/' is the subdirectory within MEDIA_ROOT where images will be stored
    # upload_to specifies the directory relative to MEDIA_ROOT
    # default provides a placeholder image if no profile picture is uploaded
    profile_picture = models.ImageField(upload_to='images/profiles/', default='images/profiles/default.jpg', blank=True, null=True)
    # Add other profile fields here if needed (e.g., bio, location)
    bio = models.TextField(max_length=500, blank=True, null=True)


    def __str__(self):
        return f'{self.user.username} Profile'

# --- Signals to automatically create/save Profile when User is created/saved ---

# Signal receiver function to create a Profile whenever a new User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Signal receiver function to save the Profile whenever the User is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if the profile exists. If not (e.g., for old users), create it first.
    # This handles users created before the create_user_profile signal was effective for them.
    if not hasattr(instance, 'profile'):
         Profile.objects.create(user=instance) # Create the profile if it's missing

    # Now that we are sure the profile exists, save it.
    instance.profile.save()