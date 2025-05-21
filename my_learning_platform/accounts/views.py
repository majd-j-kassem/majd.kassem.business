# auth_system/accounts/views.py

import secrets
import string
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.messages.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404 # <--- ENSURE get_object_or_404 IS HERE

from .models import CustomUser, Profile, TeacherCourse, CourseCategory, CourseLevel
from .forms import (
    SignupForm, CustomUserChangeForm, ProfileForm, ContactForm,
    TeacherPersonalInfoForm, TeacherProfessionalDetailsForm,
    TeacherCourseForm, # <--- ENSURE TeacherCourseForm IS HERE
    PasswordSettingForm
)

User = get_user_model() # Get your CustomUser model instance


# Import ALL your forms here, consolidated
from .forms import (
    SignupForm, CustomUserChangeForm, ProfileForm, ContactForm,
    TeacherPersonalInfoForm, TeacherProfessionalDetailsForm # Removed TeacherCourseOfferingForm
)

# Import ALL your models here, consolidated
from .models import (
    CustomUser, Profile, CourseCategory, CourseLevel, TeacherCourse
)
from .forms import (
    SignupForm, CustomUserChangeForm, ProfileForm, ContactForm,
    TeacherPersonalInfoForm, TeacherProfessionalDetailsForm,
    TeacherCourseOfferingForm, # Keep this if you're using it for add_teacher_course
    PasswordSettingForm # <<< NEW IMPORT
)

def generate_random_password(length=12):
    """Generate a secure random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))
# --- Core Homepage View ---
def index_view(request):
    print("\n--- Index View Accessed (Homepage) ---")
    context = {
        'page_title': 'Welcome to My Portfolio'
    }
    return render(request, 'index.html', context)


# --- CV Page View ---
def cv_view(request):
    print("\n--- CV View Accessed ---")
    context = {}
    return render(request, 'cv.html', context)

# --- Portfolio Page View ---
def portfolio_page_view(request):
    print("\n--- Portfolio Page View Accessed ---")
    context = {}
    return render(request, 'portfolio_page.html', context)

# --- Certificates Page View ---
def certificates_view(request):
    print("\n--- Certificates View Accessed ---")
    context = {}
    return render(request, 'certificates.html', context)

# --- Course Page View ---
def course_view(request):
    print("\n--- Course View Accessed ---")
    context = {
        'page_title': 'My Courses & Learning'
    }
    return render(request, 'courses.html', context)


# --- Contact Page View ---
def contact_view(request):
    print(f"\n--- Contact View Accessed (Method: {request.method}) ---")
    if request.method == 'POST':
        form = ContactForm(request.POST)
        print("Contact form instantiated with POST data.")
        if form.is_valid():
            print("Contact form is valid. Processing message...")
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            message_content = form.cleaned_data['message']

            try:
                subject = f'New Contact from Portfolio Site: {name}'
                body = f'Name: {name}\nEmail: {email}\n'
                if phone:
                    body += f'Phone: {phone}\n'
                body += f'\nMessage:\n{message_content}'

                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [settings.CONTACT_EMAIL]

                # send_mail(subject, body, from_email, to_email, fail_silently=False)
                print("Email sending logic executed (send_mail commented out).")

                messages.success(request, 'Your message has been sent successfully!')
                print("Contact message processed. Redirecting to contact page...")
                return redirect('contact')

            except Exception as e:
                print(f"Error processing contact message (or sending email): {e}")
                messages.error(request, 'There was an error sending your message. Please try again later.')

        else:
            print("Contact form is NOT valid.")
            messages.error(request, 'Please correct the errors below.')

    else: # GET request
        form = ContactForm()
        print("Contact form instantiated for GET.")

    context = {
        'form': form,
    }
    return render(request, 'contact.html', context)


# --- About Page View ---
def about_view(request):
    print("\n--- About View Accessed ---")
    context = {}
    return render(request, 'about.html', context)

# --- Signup View ---
def signup_view(request):
    print(f"\n--- Signup View Accessed (Method: {request.method}) ---")

    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        print("Signup form instantiated with POST and FILES.")
        if form.is_valid():
            print("Signup form is valid. Saving user and profile...")
            user = form.save()
            messages.success(request, f'Account created successfully for {user.username}! You are now logged in.')
            login(request, user)
            print("User logged in after signup. Redirecting to dashboard...")
            return redirect('dashboard')
        else:
            print("Signup form is NOT valid.")
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()
        print("Signup form instantiated for GET.")

    context = {
        'form': form,
    }
    return render(request, 'signup.html', context)


# --- Login View ---
def login_view(request):
    print(f"\n--- Login View Accessed (Method: {request.method}) ---")

    if request.method == 'GET':
        print("Handling GET request for login page.")
        storage = messages.get_messages(request)
        print(f"GET request. Messages in storage BEFORE clear: {[str(m) for m in storage]}")
        storage.used = True
        if '_messages' in request.session:
             print("GET request. '_messages' key found in session. Attempting to delete.")
             del request.session['_messages']
        else:
             print("GET request. '_messages' key not found in session initially.")

        storage = messages.get_messages(request)
        print(f"GET request. Messages in storage AFTER clear: {[str(m) for m in storage]}")
        print(f"GET request. Session keys AFTER message clear: {list(request.session.keys())}")


    if request.method == 'POST':
        print("--- Handling POST request for login ---")
        form = AuthenticationForm(request, data=request.POST)
        print("Login form instantiated with POST data.")
        if form.is_valid():
            print("Login form is valid. Attempting authentication...")
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(f"Received Username: '{username}'")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                print("Authentication successful.")
                # --- START NEW LOGIC FOR TEACHER APPROVAL ---
                if user.user_type == 'teacher': # Check if the user is a teacher
                    try:
                        profile = Profile.objects.get(user=user) # Get their profile
                        if not profile.is_teacher_approved: # If NOT approved
                            messages.error(request, "Your teacher application is pending approval. Please wait for an administrator to review it.")
                            return render(request, 'login.html', {'form': form, 'page_title': 'Login'}) # Stop login, show error
                    except Profile.DoesNotExist:
                        messages.error(request, "Your teacher profile could not be found. Please contact support.")
                        return render(request, 'accounts/login.html', {'form': form, 'page_title': 'Login'})
                # --- END NEW LOGIC ---
                login(request, user)
                print(f"Login successful. Session keys: {list(request.session.keys())}")
                messages.success(request, f'Welcome back, {user.username}!')
                print(f"Login successful. Messages in storage after login: {[str(m) for m in messages.get_messages(request)]}")
                
                # --- REVISED REDIRECT LOGIC BASED ON USER TYPE ---
                if hasattr(user, 'profile') and user.user_type == 'teacher' and user.profile.is_teacher_approved:
                    print(f"Approved Teacher '{user.username}' logged in. Redirecting to teacher_dashboard.")
                    return redirect('teacher_dashboard')
                elif user.user_type == 'student' or (user.user_type == 'teacher' and not user.profile.is_teacher_approved):
                    print(f"User '{user.username}' (Student or Pending Teacher) logged in. Redirecting to regular dashboard.")
                    return redirect('dashboard') # Regular dashboard for students or pending teachers
                else:
                    # Fallback for other user types or unexpected scenarios
                    print(f"User '{user.username}' logged in (type: {user.user_type}). Redirecting to general dashboard as fallback.")
                    return redirect('dashboard')
                # --- END REVISED LOGIC ---
            else:
                print("Authentication failed.")
                messages.error(request, 'Invalid username or password.')
        else:
            print("Login form is NOT valid.")
            print("Form errors:", form.errors) # This will show validation errors
            messages.error(request, 'Please enter a valid username and password.')

    else:
        form = AuthenticationForm()

    context = {
        'form': form,
    }
    return render(request, 'login.html', context)


# --- Logout View ---
@login_required
def logout_view(request):
    print("\n--- Logout View Accessed ---")
    logout(request)
    messages.info(request, 'You have been logged out.')
    print(f"User logged out. Messages in storage after logout: {[str(m) for m in messages.get_messages(request)]}")
    return redirect('index')


# --- Dashboard View ---
@login_required
def dashboard(request):
    print("\n--- Dashboard View Accessed ---")
    context = {
        'user': request.user,
    }
    print("Rendering dashboard template.")
    return render(request, 'dashboard.html', context)


# --- Profile Edit View ---
# --- Profile View ---
@login_required
def profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user) # Get or create profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile') # Redirect back to the profile page to show changes
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile, # Pass the profile instance to the template
        'user': user,
        'title': 'My Profile'
    }
    return render(request, 'accounts/profile.html', context)

# --- Your other views (teacher_dashboard, login_view, etc.) ---
# ...
@login_required
def profile_edit(request):
    print(f"\n--- Profile Edit View Accessed (Method: {request.method}) ---")

    if request.method == 'POST':
        print("--- Handling POST request for profile edit ---")
        try:
            user_form = CustomUserChangeForm(request.POST, instance=request.user)
            profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
            print("Forms instantiated in POST block.")

            if user_form.is_valid() and profile_form.is_valid():
                print("Forms are valid. Saving...")
                user_form.save()
                profile_form.save()
                messages.success(request, 'Your profile was successfully updated!')
                print("Forms saved. Redirecting...")
                return redirect('profile_edit')
            else:
                print("Forms are NOT valid.")
                messages.error(request, 'Please correct the errors below.')
                print(f"user_form defined after invalid POST: { 'user_form' in locals() }")
                print(f"profile_form defined after invalid POST: { 'profile_form' in locals() }")

        except Exception as e:
            print(f"An unexpected error occurred in the POST block: {e}")
            raise


    else: # GET request
        print("--- Handling GET request for profile edit ---")
        user_form = CustomUserChangeForm(instance=request.user)

        try:
            profile_instance = request.user.profile
            print(f"Profile instance retrieved for user: {profile_instance}")
            print(f"Profile instance ID: {profile_instance.id}")

            print(f"Profile Picture field value: {profile_instance.profile_picture}")
            print(f"Profile Picture URL: {profile_instance.profile_picture.url if profile_instance.profile_picture else 'None'}")
            print(f"Bio field value: '{profile_instance.bio}'")

            profile_form = ProfileForm(instance=profile_instance)
            print("ProfileForm instantiated with profile instance.")

        except Exception as e:
            print(f"Error retrieving or instantiating ProfileForm: {e}")
            profile_form = ProfileForm()
            print("ProfileForm instantiated as empty due to error.")


        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }
        print("Rendering template.")
        return render(request, 'profile.html', context)


# --- Teacher Registration Stage 1 (Basic Info) ---
def teacher_register_wizard(request):
    is_authenticated = request.user.is_authenticated

    if request.method == 'POST':
        if is_authenticated:
            form = TeacherPersonalInfoForm(request.POST,
                                           user=request.user,
                                           profile_instance=request.user.profile)
        else:
            form = TeacherPersonalInfoForm(request.POST)

        if form.is_valid():
            full_name_en = form.cleaned_data['full_name_en']
            full_name_ar = form.cleaned_data['full_name_ar']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']

            request.session['teacher_data'] = {
                'full_name_en': full_name_en,
                'full_name_ar': full_name_ar,
                'email': email,
                'phone_number': phone_number,
                'is_authenticated_at_stage1': is_authenticated
            }
            request.session.modified = True

            messages.success(request, 'Basic information saved! Proceed to the next step.')
            return redirect('teacher_register_stage2')

        else:
            messages.error(request, 'Please correct the errors below.')
    else: # GET request
        if is_authenticated:
            form = TeacherPersonalInfoForm(user=request.user, profile_instance=request.user.profile)
        else:
            form = TeacherPersonalInfoForm()

    return render(request, 'accounts/teacher_register_stage1.html', {'form': form})


# --- Teacher Registration Stage 2 (Professional Details) ---
def teacher_register_stage2(request):
    teacher_data = request.session.get('teacher_data')
    if not teacher_data:
        messages.error(request, 'Please complete the first stage of registration.')
        return redirect('teacher_register_stage1')

    is_authenticated = request.user.is_authenticated

    if request.method == 'POST':
        if is_authenticated:
            form = TeacherProfessionalDetailsForm(request.POST, profile_instance=request.user.profile)
        else:
            form = TeacherProfessionalDetailsForm(request.POST)

        if form.is_valid():
            experience_years = form.cleaned_data['experience_years']
            university = form.cleaned_data['university']
            graduation_year = form.cleaned_data['graduation_year']
            major = form.cleaned_data['major']
            bio = form.cleaned_data['bio']

            teacher_data.update({
                'experience_years': experience_years,
                'university': university,
                'graduation_year': graduation_year,
                'major': major,
                'bio': bio,
            })
            request.session['teacher_data'] = teacher_data
            request.session.modified = True

            messages.success(request, 'Professional details saved! Proceed to review.')
            # Redirect directly to stage4 (Review and Submit), skipping stage3 (Course Info)
            return redirect('teacher_register_confirm')

        else: # Form is NOT valid
            messages.error(request, 'Please correct the errors in your professional details.')
    else: # GET request
        if is_authenticated:
            form = TeacherProfessionalDetailsForm(profile_instance=request.user.profile)
        else:
            form = TeacherProfessionalDetailsForm()

    context = {
        'form': form,
    }
    return render(request, 'accounts/teacher_register_stage2.html', context)


# --- OLD/REMOVED Teacher Registration Stage 3 (Course Information Input) ---
# This function is now commented out/removed because we are skipping this stage.
# def teacher_register_stage3(request):
#     # ... (original logic for stage3) ...
#     pass


# --- Teacher Registration Stage 3 (formerly Stage 4: Review and Submit) ---
# This view now processes the teacher data from stages 1 and 2, and handles the final submission
# It NO LONGER expects course information from a previous stage
# ... (your existing imports)
from django.contrib import messages # Already there
from django.contrib.auth.models import User # Make sure User is imported if not already
from .models import Profile # Make sure Profile is imported

# In your accounts/views.py

def teacher_register_confirm(request): # Renamed from teacher_register_stage4
    """
    Handles the review stage of teacher registration.
    On POST, redirects to the password setting stage.
    """
    teacher_data = request.session.get('teacher_data')

    # Ensure previous stages were completed
    if not teacher_data:
        messages.error(request, 'Please complete all previous stages of registration.')
        return redirect('teacher_register_stage1')

    if request.method == 'POST':
        print("\n--- POST Request Received at teacher_register_confirm (Confirm) ---")
        # Just confirm and proceed to the next stage (password setting)
        # REMOVE ALL USER/PROFILE CREATION/UPDATE LOGIC FROM HERE.
        # It has been moved to teacher_register_password_setting.

        messages.info(request, 'Review confirmed. Now set your password.')
        # >>> THIS IS THE ONLY LINE YOU NEED HERE FOR POST:
        return redirect('teacher_register_password_setting') # <<< Redirect to new password setting stage

    else: # GET request for Review
        displayed_teacher_data = teacher_data.copy()

        context = {
            'teacher_data': displayed_teacher_data,
            'page_title': 'Review Your Application' # It's good to pass a title
        }
        # Keep rendering the existing template for review
        # Assuming you've renamed teacher_register_stage4.html to teacher_register_confirm.html
        # If not, keep 'accounts/teacher_register_stage4.html' for now, but rename is cleaner.
        return render(request, 'accounts/teacher_register_confirm.html', context) # Or 'accounts/teacher_register_confirm.html' if renamed

# --- New View for Application Success Page (ensure this is in your urls.py) ---
def application_success_view(request):
    """Simple view for displaying application success message."""
    return render(request, 'accounts/application_success.html', {'page_title': 'Application Submitted'})
# --- Helper Functions (like is_approved_teacher, should be defined here, BEFORE views) ---
def is_approved_teacher(user):
    """
    Test to check if the user is a teacher and their application is approved.
    Also checks if the profile exists to prevent AttributeError.
    """
    return user.is_authenticated and user.user_type == 'teacher' and \
           hasattr(user, 'profile') and user.profile.is_teacher_approved


# ... (Your other views like index_view, login_view, dashboard, etc.) ...

# --- NEW: Add Course View (for Approved Teachers) ---
@login_required
@user_passes_test(is_approved_teacher, login_url='/login/')
def add_teacher_course(request):
    """
    Allows an approved teacher to add a new course.
    """
    # Get the teacher's profile. If not found, it's a critical error for an approved teacher.
    teacher_profile = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':
        # When handling forms with files (ImageField), you MUST pass request.FILES
        form = TeacherCourseForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Save the course instance, but don't commit to the database yet.
                # We need to set the teacher_profile before saving.
                course = form.save(commit=False)
                course.teacher_profile = teacher_profile # Assign the logged-in teacher's profile
                course.status = 'pending' # Default to pending review upon creation
                course.save() # Now save the instance to the database

                # For ManyToMany relationships (like 'categories'), save them after the instance is saved.
                form.save_m2m()

                messages.success(request, 'Your course has been submitted for review successfully!')
                return redirect('teacher_dashboard') # Redirect to the teacher's dashboard
            except Exception as e:
                messages.error(request, f'An unexpected error occurred while saving the course: {e}')
                # Log the full traceback for debugging purposes
                import traceback
                traceback.print_exc()
        else:
            messages.error(request, 'Please correct the errors below.')
    else: # GET request, display an empty form
        form = TeacherCourseForm()

    context = {
        'form': form,
        'page_title': 'Add New Course',
    }
    return render(request, 'accounts/add_teacher_course.html', context)

# ... (Your other views like teacher_dashboard, edit_teacher_course, delete_teacher_course etc.) ...
def teacher_register_password_setting(request):
    """
    Handles setting the password for new teacher accounts and finalizes submission.
    """
    teacher_data = request.session.get('teacher_data')

    # Ensure previous stages were completed
    if not teacher_data:
        messages.error(request, 'Please complete all previous stages of registration.')
        return redirect('teacher_register_stage1')

    # For authenticated users (existing users applying as teacher), they don't set a password here.
    # They should manage their password via profile edit.
    # We will assume this stage is primarily for NEW users.
    is_authenticated = teacher_data.get('is_authenticated_at_stage1')
    if is_authenticated and request.user.is_authenticated:
        # If an authenticated user reaches here, it means they are trying to apply as a teacher.
        # They should not be prompted to set a password.
        # Instead, we should just finalize their application (update profile) directly.
        # Re-use the user/profile update logic from below.
        user = request.user
        profile, created_profile = Profile.objects.get_or_create(user=user)
        if created_profile:
            messages.info(request, "New profile created for your existing account.")
        else:
            messages.info(request, "Updating existing profile.")

        # Update all profile fields from session data (these are already defined from teacher_data)
        profile.full_name_en = teacher_data.get('full_name_en', profile.full_name_en)
        profile.full_name_ar = teacher_data.get('full_name_ar', profile.full_name_ar)
        profile.phone_number = teacher_data.get('phone_number', profile.phone_number)
        profile.experience_years = teacher_data.get('experience_years', profile.experience_years)
        profile.university = teacher_data.get('university', profile.university)
        profile.graduation_year = teacher_data.get('graduation_year', profile.graduation_year)
        profile.major = teacher_data.get('major', profile.major)
        profile.bio = teacher_data.get('bio', profile.bio)

        # Set user_type to 'teacher' if it's not already
        if user.user_type != 'teacher':
            user.user_type = 'teacher'
            user.save()
            print(f"User type updated to 'teacher' for {user.username}")

        profile.is_teacher_application_pending = True
        profile.is_teacher_approved = False
        profile.approved_by = None
        profile.approval_date = None
        profile.rejected_by = None
        profile.rejection_date = None
        profile.rejection_reason = None

        try:
            profile.save()
            if 'teacher_data' in request.session:
                del request.session['teacher_data']
                request.session.modified = True
            messages.success(request, 'Your teacher application has been submitted successfully and is awaiting approval!')
            return redirect('application_success')
        except Exception as e:
            messages.error(request, f"An error occurred while saving your teacher profile: {e}")
            import traceback
            traceback.print_exc()
            return redirect('teacher_register_stage1')


    if request.method == 'POST':
        print("\n--- POST Request Received at teacher_register_password_setting ---")
        form = PasswordSettingForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['password']

            full_name_en = teacher_data.get('full_name_en')
            full_name_ar = teacher_data.get('full_name_ar')
            email = teacher_data.get('email')
            phone_number = teacher_data.get('phone_number')
            experience_years = teacher_data.get('experience_years')
            university = teacher_data.get('university')
            graduation_year = teacher_data.get('graduation_year')
            major = teacher_data.get('major')
            bio = teacher_data.get('bio')

            user = None # Initialize user to None for this path

            try:
                # This logic is for NEW users only at this stage
                try:
                    user = CustomUser.objects.get(email=email)
                    messages.warning(request, "An account with this email already exists. Please log in to update your profile.")
                    print(f"Account with email '{email}' already exists. Redirecting to login.")
                    # This scenario should ideally be caught earlier (e.g., in stage1 or stage4)
                    # but as a fallback, ensure we don't try to create a duplicate user.
                    return redirect('login')
                except CustomUser.DoesNotExist:
                    # Create a new user with the chosen password
                    username_base = email.split('@')[0]
                    username = username_base
                    i = 1
                    while CustomUser.objects.filter(username=username).exists():
                        username = f"{username_base}{i}"
                        i += 1

                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password, # <<< Use the user-set password here!
                        user_type='teacher',
                        is_active=True,
                    )
                    messages.success(request, f"New account created for '{user.username}'.")
                    print(f"NEW User created: {user.username}, Password Set by User.")

                # Now, get or create the profile for the user
                profile, created_profile = Profile.objects.get_or_create(user=user)
                if created_profile:
                    print(f"Profile {profile.pk} was newly created (by get_or_create).")
                else:
                    print(f"Existing profile {profile.pk} fetched.")


                # Update all profile fields from session data
                profile.full_name_en = full_name_en
                profile.full_name_ar = full_name_ar
                profile.phone_number = phone_number
                profile.experience_years = experience_years
                profile.university = university
                profile.graduation_year = graduation_year
                profile.major = major
                profile.bio = bio

                # Set application status
                profile.is_teacher_application_pending = True
                profile.is_teacher_approved = False
                profile.approved_by = None
                profile.approval_date = None
                profile.rejected_by = None
                profile.rejection_date = None
                profile.rejection_reason = None

                profile.save()
                print(f"\n--- Profile SUCCESSFULLY SAVED! ID: {profile.pk} ---")

                # Clear session data after successful submission
                if 'teacher_data' in request.session:
                    del request.session['teacher_data']
                    request.session.modified = True
                    print("Teacher data cleared from session.")

                messages.success(request, 'Your teacher application has been submitted successfully and is awaiting approval! You can now log in.')
                return redirect('application_success') # Redirect to success page

            except Exception as e:
                messages.error(request, f"An error occurred during account creation/submission: {e}")
                print(f"\n!!! ERROR DURING FINAL SUBMISSION: {e} !!!")
                import traceback
                traceback.print_exc()
                return redirect('teacher_register_stage1') # Send back to stage 1 on critical error

        else: # Form is NOT valid
            messages.error(request, 'Please correct the password errors below.')
            print("PasswordSettingForm errors:", form.errors) # Debug password form errors

    else: # GET request
        form = PasswordSettingForm() # Instantiate empty form for GET

    context = {
        'form': form,
        'page_title': 'Set Your Password'
    }
    return render(request, 'accounts/teacher_register_password_setting.html', context)

@login_required
@user_passes_test(lambda user: user.user_type == 'teacher' and user.profile.is_teacher_approved)
def teacher_dashboard(request):
    # This is a placeholder for the teacher's dashboard content
    # You can fetch courses taught by the teacher, pending requests, etc.
    teacher_profile = request.user.profile
    teacher_courses = TeacherCourse.objects.filter(teacher_profile=teacher_profile)

    context = {
        'teacher_profile': teacher_profile,
        'teacher_courses': teacher_courses,
        'title': 'Teacher Dashboard',
    }
    return render(request, 'teacher_dashboard.html', context)

# --- Your other views (login_view, logout_view, signup_view, profile_view, etc.) ---
# ...
