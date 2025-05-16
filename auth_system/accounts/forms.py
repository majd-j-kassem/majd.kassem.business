# auth_system/accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import Profile # Import the new Profile model

# Get the currently active User model (handles custom user models if you ever use one)
User = get_user_model()

# --- Signup Form (Updated to include profile_picture and bio) ---
class SignupForm(UserCreationForm):
    # Add the profile_picture field directly to the form
    # This field is NOT part of the User model, so it's not in the Meta class fields.
    # We will handle saving this field manually in the form's save method.
    profile_picture = forms.ImageField(required=False, label="Profile Picture")
    bio = forms.CharField(max_length=500, required=False, label="Bio", widget=forms.Textarea)


    class Meta(UserCreationForm.Meta):
        model = User
        # Include fields from the User model here.
        # 'profile_picture' and 'bio' are NOT User model fields, so they are not listed here.
        fields = UserCreationForm.Meta.fields + ('email', 'first_name', 'last_name') # Added first/last name for signup
        # Example of adding other User model fields if needed:
        # fields = ('username', 'first_name', 'last_name', 'email') + UserCreationForm.Meta.fields


    # Optional: You can override the clean methods for custom validation
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    # Custom save method to handle saving the profile picture and bio
    # This method is called from the signup_view after form.is_valid()
    def save(self, commit=True):
        # First, save the User instance using the parent class's save method
        user = super().save(commit=commit)

        # If commit is True, the user is saved to the database.
        # The post_save signal for User should then create the associated Profile.
        # We can then get the profile and save the profile_picture and bio.
        if commit:
            # Get the related profile instance (created by the signal)
            # We use get_or_create just in case the signal didn't fire for some reason,
            # though the signal should guarantee it exists here.
            profile, created = Profile.objects.get_or_create(user=user)

            # Save the profile_picture if it was provided in the form
            if 'profile_picture' in self.cleaned_data and self.cleaned_data['profile_picture']:
                 profile.profile_picture = self.cleaned_data['profile_picture']

            # Save the bio if it was provided in the form
            if 'bio' in self.cleaned_data and self.cleaned_data['bio']:
                 profile.bio = self.cleaned_data['bio']

            profile.save() # Save the updated profile instance

        return user


# --- User Profile Change Form (Keep this as is) ---
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password', None)


# --- Profile Form for Profile Model fields (Keep this as is) ---
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio']
