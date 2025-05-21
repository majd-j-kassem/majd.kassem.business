# auth_system/accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from .models import Profile # Import the new Profile model
from .models import Profile, CourseCategory, CourseLevel # <-- THIS LINE IS CRUCIAL

from .models import TeacherCourse, CourseCategory, CourseLevel

# Get the currently active User model (handles custom user models if you ever use one)
User = get_user_model()

# --- Teacher Personal Information Form ---
class TeacherPersonalInfoForm(forms.ModelForm):
    # The 'email' field is on CustomUser, so we add it explicitly to this form
    # It allows us to combine fields from different models in one form.
    email = forms.EmailField(label="Email", required=False)
    

    class Meta:
        model = Profile # This form primarily manages Profile fields
        fields = ['full_name_en', 'full_name_ar', 'phone_number']
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.profile_instance = kwargs.pop('profile_instance', None)
        super().__init__(*args, **kwargs)

        # Explicitly make these fields required in the form.
        # This overrides any `blank=True` or `null=True` settings on the model fields
        # at the form validation level, forcing the user to provide a value.
        '''
        self.fields['full_name_en'].required = True
        self.fields['full_name_ar'].required = True
        self.fields['phone_number'].required = True
        '''

        # Pre-populate initial values if a user or profile instance is provided
        if self.user:
            self.fields['email'].initial = self.user.email
        if self.profile_instance:
            self.fields['full_name_en'].initial = self.profile_instance.full_name_en
            self.fields['full_name_ar'].initial = self.profile_instance.full_name_ar
            self.fields['phone_number'].initial = self.profile_instance.phone_number


    # Override save method to handle saving data to both CustomUser (for email) and Profile
    def save(self, commit=True):
        # Save the Profile instance first
        profile = super().save(commit=False)

        # Update the user's email if it has changed
        if self.user and self.cleaned_data['email'] != self.user.email:
            self.user.email = self.cleaned_data['email']
            self.user.save()

        if commit:
            profile.save() # Save the profile instance to the database
        return profile


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
        
# --- Contact Form ---
class ContactForm(forms.Form):
    """
    Form for users to submit contact messages.
    """
    name = forms.CharField(
        label='Your Name',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your name'})
    )
    email = forms.EmailField(
        label='Your Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'})
    )
    phone = forms.CharField(
        label='Your Phone Number (Optional)',
        max_length=20,
        required=False, # Make phone number optional
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number (optional)'})
    )
    message = forms.CharField(
        label='Your Message',
        widget=forms.Textarea(attrs={'placeholder': 'Enter your message', 'rows': 6})
    )

class TeacherProfessionalDetailsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['experience_years', 'university', 'graduation_year', 'major', 'bio']

    # You can add custom validation or initial data here if needed.
    def __init__(self, *args, **kwargs):
        # We pass a profile instance to the form if we want to pre-populate it
        self.profile_instance = kwargs.pop('profile_instance', None)
        super().__init__(*args, **kwargs)

        # Pre-populate fields if a profile instance is provided
        if self.profile_instance:
            self.fields['experience_years'].initial = self.profile_instance.experience_years
            self.fields['university'].initial = self.profile_instance.university
            self.fields['graduation_year'].initial = self.profile_instance.graduation_year
            self.fields['major'].initial = self.profile_instance.major
            self.fields['bio'].initial = self.profile_instance.bio

        # You can make fields required here if needed, e.g.:
        # self.fields['university'].required = True
# --- NEW Teacher Course Offering Form ---
class TeacherCourseOfferingForm(forms.Form): # Not a ModelForm if it's for creation
    categories = forms.ModelMultipleChoiceField(
        queryset=CourseCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple, # Or forms.SelectMultiple for a dropdown
        label="Course Categories",
        help_text="Select all categories that apply to your course."
    )
    level = forms.ModelChoiceField(
        queryset=CourseLevel.objects.all(),
        empty_label="Select Level",
        label="Course Level",
        help_text="Difficulty level of your course."
    )
    title = forms.CharField(
        max_length=255,
        label="Course Title",
        help_text="A descriptive title for your course."
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Course Description",
        help_text="Provide a detailed description of what your course covers."
    )
    price = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        label="Course Price ($)",
        min_value=0.01,
        help_text="Price per student for your course."
    )
    language = forms.CharField(
        max_length=100,
        label="Instruction Language",
        help_text="The primary language of instruction for this course."
    )

    # You can add clean methods for validation here if needed
class PasswordSettingForm(forms.Form):
    password = forms.CharField(
        label=("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False, # Important for password fields
        help_text=("Your password must contain at least 8 characters.")
    )
    password_confirm = forms.CharField(
        label=("Confirm Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError(
                    ("The two password fields didn't match.")
                )
            # You can add more password validation rules here (e.g., complexity)
            # if they are not already handled by your CustomUser model validators.
            if len(password) < 8:
                raise forms.ValidationError(
                    ("Your password must be at least 8 characters long.")
                )
        return cleaned_data
class TeacherCourseForm(forms.ModelForm):
    # For ManyToMany fields like 'categories', it's often better to use ModelMultipleChoiceField
    # with a CheckboxSelectMultiple widget for a multi-select checkbox UI.
    categories = forms.ModelMultipleChoiceField(
        queryset=CourseCategory.objects.all().order_by('name'), # Order for consistent display
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select one or more categories for your course."
    )

    # For ForeignKey fields like 'level', ModelChoiceField is used by default with a Select widget.
    level = forms.ModelChoiceField(
        queryset=CourseLevel.objects.all().order_by('name'), # Order for consistent display
        required=True,
        empty_label="Select a level",
        help_text="Choose the appropriate level for your course."
    )

    class Meta:
        model = TeacherCourse
        fields = [
            'title',
            'description',
            'price',
            'language',
            'categories',
            'level',
            'course_picture',
            'video_trailer_url',
            # 'status' is managed by the system, not directly by the teacher in this form
            # 'created_at', 'updated_at' are auto-managed
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00'}),
            'language': forms.TextInput(attrs={'placeholder': 'e.g., English, Arabic'}),
            'video_trailer_url': forms.URLInput(attrs={'placeholder': 'e.g., https://www.youtube.com/watch?v=xxxxxxxx'}),
        }
        labels = {
            'title': 'Course Title',
            'description': 'Course Description',
            'price': 'Price ($)',
            'language': 'Language of Instruction',
            'categories': 'Course Categories',
            'level': 'Course Level',
            'course_picture': 'Course Thumbnail/Cover Image',
            'video_trailer_url': 'Video Trailer URL (Optional)',
        }
        help_texts = {
            'title': 'A clear and engaging title for your course.',
            'description': 'Provide a comprehensive description of what your course covers.',
            'course_picture': 'Upload a clear image to represent your course.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap form-control class to most fields for consistent styling
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.NumberInput, forms.URLInput, forms.Select, forms.FileInput)):
                field.widget.attrs['class'] = 'form-control'
            # CheckboxSelectMultiple is handled differently in the template for better styling
            # If you want default styling for each checkbox, you might add:
            # elif isinstance(field.widget, forms.CheckboxInput):
            #     field.widget.attrs['class'] = 'form-check-input'
class PaymentForm(forms.Form):
    card_number = forms.CharField(label='Card Number', max_length=16, min_length=16,
                                  widget=forms.TextInput(attrs={'placeholder': '•••• •••• •••• ••••', 'pattern': '[0-9]{16}', 'title': '16-digit card number', 'inputmode': 'numeric'}))
    cardholder_name = forms.CharField(label='Cardholder Name', max_length=100,
                                      widget=forms.TextInput(attrs={'placeholder': 'Full Name'}))
    expiry_month = forms.ChoiceField(label='Expiry Month', choices=[(i, f'{i:02d}') for i in range(1, 13)])
    expiry_year = forms.ChoiceField(label='Expiry Year', choices=[(i, str(i)) for i in range(2025, 2036)]) # Adjust years as needed
    cvv = forms.CharField(label='CVV', max_length=3, min_length=3,
                          widget=forms.TextInput(attrs={'placeholder': '•••', 'pattern': '[0-9]{3,4}', 'title': '3 or 4-digit CVV', 'inputmode': 'numeric'}))
# --- Add these forms if they are missing or incomplete ---

class UserLoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'placeholder': 'Your Username'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Your Password'})
    )

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password'})
    )
    password2 = forms.CharField(
        label='Repeat Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email