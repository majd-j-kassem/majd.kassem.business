# auth_system/accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
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
                login(request, user)
                print(f"Login successful. Session keys: {list(request.session.keys())}")
                messages.success(request, f'Welcome back, {user.username}!')
                print(f"Login successful. Messages in storage after login: {[str(m) for m in messages.get_messages(request)]}")
                return redirect('courses')
            else:
                print("Authentication failed.")
                messages.error(request, 'Invalid username or password.')
        else:
            print("Login form is NOT valid.")
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
            return redirect('teacher_register_stage4')

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

def teacher_register_stage4(request):
    """
    Handles the final stage of teacher registration,
    creating/updating user and profile, and setting application status.
    """
    teacher_data = request.session.get('teacher_data')

    # Ensure previous stages were completed
    if not teacher_data:
        messages.error(request, 'Please complete all previous stages of registration.')
        return redirect('teacher_register_stage1')

    if request.method == 'POST':
        print("\n--- POST Request Received at Stage 4 ---")
        print(f"Session Teacher Data: {teacher_data}") # Debug: See what's in the session

        is_authenticated = teacher_data.get('is_authenticated_at_stage1')
        user = None
        profile = None

        try:
            # Path 1: User is already logged in (e.g., existing user applying as teacher)
            if is_authenticated and request.user.is_authenticated:
                user = request.user
                # Check if profile exists; if not, create it (shouldn't happen often if OneToOne)
                profile, created = Profile.objects.get_or_create(user=user)
                if created:
                    print(f"Created new profile for existing user: {user.username}")
                    messages.info(request, "New profile created for your account.")
                else:
                    messages.info(request, "Updating existing profile.")
                print(f"Existing User: {user.username}, Profile ID: {profile.pk}")

            # Path 2: New user applying (not logged in, email does not exist yet)
            else:
                email = teacher_data.get('email')
                if not email:
                    raise ValueError("Email is required to create a new user.")

                try:
                    # Check if an account with this email already exists
                    user = CustomUser.objects.get(email=email)
                    messages.warning(request, "An account with this email already exists. Please log in to update your profile.")
                    print(f"Account with email '{email}' already exists. Redirecting to login.")
                    return redirect('login') # Redirect away if email already exists
                except CustomUser.DoesNotExist:
                    # Create a new user (and generate a unique username)
                    username_base = email.split('@')[0]
                    username = username_base
                    i = 1
                    while CustomUser.objects.filter(username=username).exists():
                        username = f"{username_base}{i}"
                        i += 1
                    user = CustomUser.objects.create_user(username=username, email=email, password=CustomUser.objects.make_random_password())

                    user.is_active = True # Or set to False if you require email verification
                    # Assuming user_type is handled later or defaults correctly
                    user.save()
                    profile = Profile.objects.create(user=user) # Create a new profile linked to the new user
                    messages.success(request, "New account created. Please remember your username/password (randomly generated for now).")
                    print(f"NEW User created: {user.username}, Profile ID: {profile.pk}")

        except Exception as e:
            messages.error(request, f"An error occurred during user/profile creation/retrieval: {e}")
            print(f"ERROR during user/profile creation/retrieval: {e}") # Print error to console
            import traceback
            traceback.print_exc() # Print full traceback
            return redirect('teacher_register_stage1') # Send back to stage 1 on critical error

        # --- Update Profile fields from session data (This runs for both new and existing profiles) ---
        if profile: # Ensure profile object was successfully created or retrieved
            profile.full_name_en = teacher_data.get('full_name_en', profile.full_name_en)
            profile.full_name_ar = teacher_data.get('full_name_ar', profile.full_name_ar)
            profile.phone_number = teacher_data.get('phone_number', profile.phone_number)
            profile.experience_years = teacher_data.get('experience_years', profile.experience_years)
            profile.university = teacher_data.get('university', profile.university)
            profile.graduation_year = teacher_data.get('graduation_year', profile.graduation_year)
            profile.major = teacher_data.get('major', profile.major)
            profile.bio = teacher_data.get('bio', profile.bio)

            # Set user_type to 'teacher' during application submission
            if user.user_type != 'teacher': # Only change if not already teacher
                user.user_type = 'teacher'
                user.save() # Save user if user_type changed
                print(f"User type updated to 'teacher' for {user.username}")

            # Set the application status to pending for admin review
            profile.is_teacher_application_pending = True
            profile.is_teacher_approved = False # Ensure it's not approved initially

            # --- Debugging prints before saving ---
            print("\n--- Profile Data BEFORE Final Save ---")
            print(f"Profile Object: {profile}")
            print(f"Profile ID (before save attempt): {profile.pk}")
            print(f"Full Name EN: {profile.full_name_en}")
            print(f"Phone Number: {profile.phone_number}")
            print(f"Is Teacher Application Pending: {profile.is_teacher_application_pending}")
            print(f"Is Teacher Approved: {profile.is_teacher_approved}")
            print(f"Related User's Type: {profile.user.user_type}")

            try:
                profile.save() # <-- THIS IS THE CRITICAL LINE THAT PERSISTS CHANGES
                print(f"\n--- Profile SUCCESSFULLY SAVED! ID: {profile.pk} ---")

                # Clear session data after successful submission
                if 'teacher_data' in request.session:
                    del request.session['teacher_data']
                    request.session.modified = True
                    print("Teacher data cleared from session.")

                messages.success(request, 'Your teacher application has been submitted successfully and is awaiting approval!')
                return redirect('application_success') # Redirect to success page

            except Exception as e:
                messages.error(request, f"An error occurred while saving your teacher profile: {e}")
                print(f"\n!!! ERROR SAVING PROFILE: {e} !!!")
                import traceback
                traceback.print_exc() # Print full traceback to console
                return redirect('teacher_register_stage1') # Redirect or re-render form with errors

        else: # If for some reason profile was not obtained or created
            messages.error(request, "Failed to retrieve or create user profile for update.")
            return redirect('teacher_register_stage1')

    else: # GET request for Stage 4 (Review)
        # Display collected data from previous stages
        displayed_teacher_data = teacher_data.copy()

        context = {
            'teacher_data': displayed_teacher_data,
        }
        return render(request, 'accounts/teacher_register_stage4.html', context)

# --- New View for Application Success Page (ensure this is in your urls.py) ---
def application_success_view(request):
    """Simple view for displaying application success message."""
    return render(request, 'accounts/application_success.html', {})

# --- NEW: Add Course View (for Approved Teachers) ---
@login_required
def add_teacher_course(request):
    # Ensure user is a teacher and is approved
    if not hasattr(request.user, 'profile') or request.user.user_type != 'teacher' or not request.user.profile.is_teacher_approved:
        messages.error(request, "You must be an approved teacher to add a course.")
        return redirect('dashboard') # Or a page indicating denial

    if request.method == 'POST':
        form = TeacherCourseOfferingForm(request.POST)
        if form.is_valid():
            new_course = form.save(commit=False)
            new_course.teacher_profile = request.user.profile # Assign the current teacher's profile
            new_course.save()
            form.save_m2m() # Save ManyToMany relationships (categories)

            messages.success(request, "Your course has been added successfully!")
            return redirect('dashboard') # Redirect to teacher's dashboard or course list
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = TeacherCourseOfferingForm()

    context = {
        'form': form,
        'page_title': 'Add New Course'
    }
    return render(request, 'accounts/add_teacher_course.html', context)