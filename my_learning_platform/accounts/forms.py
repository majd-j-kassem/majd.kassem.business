# my_learning_platform/accounts/forms.py (or auth_system/accounts/forms.py, depending on your setup)

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from datetime import datetime

# Make sure these imports correctly point to your models
from .models import Profile, CourseCategory, CourseLevel, TeacherCourse 

# Get the currently active User model
User = get_user_model()

# --- Teacher Personal Information Form ---
class TeacherPersonalInfoForm(forms.ModelForm):
    email = forms.EmailField(label="Email", required=False)
    
    class Meta:
        model = Profile
        fields = ['full_name_en', 'full_name_ar', 'phone_number']
        widgets = {
            'full_name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name_ar': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.profile_instance = kwargs.pop('profile_instance', None)
        super().__init__(*args, **kwargs)
        # Add class to email field as it's not in Meta.widgets
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

        if self.user:
            self.fields['email'].initial = self.user.email
        if self.profile_instance:
            self.fields['full_name_en'].initial = self.profile_instance.full_name_en
            self.fields['full_name_ar'].initial = self.profile_instance.full_name_ar
            self.fields['phone_number'].initial = self.profile_instance.phone_number

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user and self.cleaned_data['email'] != self.user.email:
            self.user.email = self.cleaned_data['email']
            self.user.save()

        if commit:
            profile.save()
        return profile


# --- Signup Form (Updated to include profile_picture and bio) ---
class SignupForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False, label="Profile Picture", widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))
    bio = forms.CharField(max_length=500, required=False, label="Bio", widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    full_name_en = forms.CharField(max_length=255, required=False, label="Full Name (Eng)", widget=forms.TextInput(attrs={'class': 'form-control'}))
    full_name_ar = forms.CharField(max_length=255, required=False, label="Full Name (Ar)", widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'}),
        }
        
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)

        if commit:
            profile, created = Profile.objects.get_or_create(user=user)

            if 'profile_picture' in self.cleaned_data and self.cleaned_data['profile_picture']:
                 profile.profile_picture = self.cleaned_data['profile_picture']

            if 'bio' in self.cleaned_data and self.cleaned_data['bio']:
                 profile.bio = self.cleaned_data['bio']
            
            profile.full_name_en = self.cleaned_data['full_name_en']
            profile.full_name_ar = self.cleaned_data['full_name_ar']

            profile.save()

        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('password', None)


# --- Profile Form for Profile Model fields ---
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'profile_picture',
            'bio',
            'full_name_en',
            'full_name_ar',
            'phone_number',
            'experience_years',
            'university',
            'graduation_year',
            'major',
        ]
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'full_name_en': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name_ar': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'university': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': datetime.now().year}),
            'major': forms.TextInput(attrs={'class': 'form-control'}),
        }


# --- Contact Form ---
class ContactForm(forms.Form):
    name = forms.CharField(
        label='Your Name',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your name', 'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Your Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address', 'class': 'form-control'})
    )
    phone = forms.CharField(
        label='Your Phone Number (Optional)',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number (optional)', 'class': 'form-control'})
    )
    message = forms.CharField(
        label='Your Message',
        widget=forms.Textarea(attrs={'placeholder': 'Enter your message', 'rows': 6, 'class': 'form-control'})
    )

class TeacherProfessionalDetailsForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['experience_years', 'university', 'graduation_year', 'major', 'bio']
        widgets = {
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'university': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control', 'min': 1900, 'max': datetime.now().year}),
            'major': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.profile_instance = kwargs.pop('profile_instance', None)
        super().__init__(*args, **kwargs)

        if self.profile_instance:
            self.fields['experience_years'].initial = self.profile_instance.experience_years
            self.fields['university'].initial = self.profile_instance.university
            self.fields['graduation_year'].initial = self.profile_instance.graduation_year
            self.fields['major'].initial = self.profile_instance.major
            self.fields['bio'].initial = self.profile_instance.bio

class TeacherCourseOfferingForm(forms.Form):
    categories = forms.ModelMultipleChoiceField(
        queryset=CourseCategory.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Course Categories",
        help_text="Select all categories that apply to your course."
    )
    level = forms.ModelChoiceField(
        queryset=CourseLevel.objects.all(),
        empty_label="Select Level",
        label="Course Level",
        help_text="Difficulty level of your course.",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    title = forms.CharField(
        max_length=255,
        label="Course Title",
        help_text="A descriptive title for your course.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        label="Course Description",
        help_text="Provide a detailed description of what your course covers."
    )
    price = forms.DecimalField(
        max_digits=8,
        decimal_places=2,
        label="Course Price ($)",
        min_value=0.01,
        help_text="Price per student for your course.",
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'class': 'form-control'})
    )
    language = forms.CharField(
        max_length=100,
        label="Instruction Language",
        help_text="The primary language of instruction for this course.",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

class PasswordSettingForm(forms.Form):
    password = forms.CharField(
        label=("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
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
            if len(password) < 8:
                raise forms.ValidationError(
                    ("Your password must be at least 8 characters long.")
                )
        return cleaned_data

class TeacherCourseForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=CourseCategory.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text="Select one or more categories for your course."
    )

    level = forms.ModelChoiceField(
        queryset=CourseLevel.objects.all().order_by('name'),
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
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.00', 'class': 'form-control'}),
            'language': forms.TextInput(attrs={'placeholder': 'e.g., English, Arabic', 'class': 'form-control'}),
            'video_trailer_url': forms.URLInput(attrs={'placeholder': 'e.g., https://www.youtube.com/watch?v=xxxxxxxx', 'class': 'form-control'}),
            'course_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
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
        # For CheckboxSelectMultiple and Select, default styling might be slightly different.
        # Ensure the 'form-control' class is applied for general inputs.
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, (forms.CheckboxSelectMultiple, forms.RadioSelect)):
                if 'class' not in field.widget.attrs:
                    field.widget.attrs['class'] = 'form-control'
                else:
                    # Append 'form-control' if other classes exist
                    field.widget.attrs['class'] += ' form-control'


class PaymentForm(forms.Form):
    card_number = forms.CharField(
        label='Card Number',
        max_length=255,
        widget=forms.TextInput(attrs={
            'placeholder': '•••• •••• •••• •••• ••••',
            'pattern': '[0-9]*',
            'title': 'Card number (digits only)',
            'inputmode': 'numeric',
            'class': 'form-control'
        })
    )
    expiry_month = forms.ChoiceField(label='Expiry Month', choices=[(i, f'{i:02d}') for i in range(1, 13)], widget=forms.Select(attrs={'class': 'form-control'}))
    expiry_year = forms.ChoiceField(label='Expiry Year', choices=[(i, str(i)) for i in range(datetime.now().year, datetime.now().year + 11)], widget=forms.Select(attrs={'class': 'form-control'}))

class UserLoginForm(forms.Form):
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'placeholder': 'Your Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Your Password', 'class': 'form-control'})
    )

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password', 'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Repeat Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


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