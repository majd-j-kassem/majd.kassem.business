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
    TeacherPersonalInfoForm, TeacherProfessionalDetailsForm, TeacherCourseOfferingForm # <-- NEW FORM
)

# Import ALL your models here, consolidated
from .models import (
    CustomUser, Profile, CourseCategory, CourseLevel, TeacherCourse # <-- NEW MODELS
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

            messages.success(request, 'Professional details saved! Proceed to the next step.')
            return redirect('teacher_register_stage3') # Redirect to the NEW Stage 3

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


# --- NEW Teacher Registration Stage 3 (Course Information Input) ---
def teacher_register_stage3(request): # This is the NEW function for Course Info
    teacher_data = request.session.get('teacher_data')
    if not teacher_data:
        messages.error(request, 'Please complete the previous stages of registration.')
        return redirect('teacher_register_stage1')

    if request.method == 'POST':
        form = TeacherCourseOfferingForm(request.POST)
        if form.is_valid():
            course_info = {
                'categories': [category.id for category in form.cleaned_data['categories']],
                'level': form.cleaned_data['level'].id,
                'title': form.cleaned_data['title'],
                'description': form.cleaned_data['description'],
                'price': str(form.cleaned_data['price']),
                'language': form.cleaned_data['language'],
            }
            teacher_data.update(course_info)
            request.session['teacher_data'] = teacher_data
            request.session.modified = True

            messages.success(request, 'Course information saved! Proceed to review.')
            return redirect('teacher_register_stage4') # Redirect to NEW Stage 4

        else:
            messages.error(request, 'Please correct the errors in your course details.')
    else: # GET request
        form = TeacherCourseOfferingForm()

    context = { 'form': form }
    return render(request, 'accounts/teacher_register_stage3.html', context)


# --- NEW Teacher Registration Stage 4 (Review and Submit) ---
def teacher_register_stage4(request): # This is the NEW function for Review & Submit
    teacher_data = request.session.get('teacher_data')

    if not teacher_data:
        messages.error(request, 'Please complete all previous stages of registration.')
        return redirect('teacher_register_stage1')

    if request.method == 'POST':
        is_authenticated = teacher_data.get('is_authenticated_at_stage1')

        try:
            if is_authenticated and request.user.is_authenticated:
                user = request.user
                profile = user.profile
                messages.info(request, "Updating existing profile.")
            else:
                email = teacher_data.get('email')
                if not email:
                    raise ValueError("Email is required to create a new user.")

                try:
                    user = User.objects.get(email=email)
                    messages.warning(request, "An account with this email already exists. Please log in to update your profile.")
                    return redirect('login')
                except User.DoesNotExist:
                    username_base = email.split('@')[0]
                    username = username_base
                    i = 1
                    while User.objects.filter(username=username).exists():
                        username = f"{username_base}{i}"
                        i += 1

                    user = User.objects.create_user(username=username, email=email, password=User.objects.make_random_password())
                    user.is_active = True
                    user.save()
                    profile = Profile.objects.create(user=user)
                    messages.success(request, "New account created. Please remember your username/password (randomly generated for now).")

        except Exception as e:
            messages.error(request, f"An error occurred during user/profile creation: {e}")
            return redirect('teacher_register_stage1')

        profile.full_name_en = teacher_data.get('full_name_en', profile.full_name_en)
        profile.full_name_ar = teacher_data.get('full_name_ar', profile.full_name_ar)
        profile.phone_number = teacher_data.get('phone_number', profile.phone_number)
        profile.experience_years = teacher_data.get('experience_years', profile.experience_years)
        profile.university = teacher_data.get('university', profile.university)
        profile.graduation_year = teacher_data.get('graduation_year', profile.graduation_year)
        profile.major = teacher_data.get('major', profile.major)
        profile.bio = teacher_data.get('bio', profile.bio)
        profile.save()

        course_categories_ids = teacher_data.get('categories', [])
        course_level_id = teacher_data.get('level')

        categories = CourseCategory.objects.filter(id__in=course_categories_ids)
        level = CourseLevel.objects.get(id=course_level_id) if course_level_id else None

        new_course = TeacherCourse.objects.create(
            teacher_profile=profile,
            level=level,
            title=teacher_data.get('title'),
            description=teacher_data.get('description'),
            price=teacher_data.get('price'),
            language=teacher_data.get('language'),
        )
        new_course.categories.set(categories)

        if 'teacher_data' in request.session:
            del request.session['teacher_data']
            request.session.modified = True

        messages.success(request, 'Your teacher application has been submitted successfully!')
        return redirect('application_success')

    else: # GET request for Stage 4 (Review)
        displayed_teacher_data = teacher_data.copy()
        if 'categories' in displayed_teacher_data:
            category_ids = displayed_teacher_data['categories']
            displayed_teacher_data['categories_names'] = list(CourseCategory.objects.filter(id__in=category_ids).values_list('name', flat=True))
        if 'level' in displayed_teacher_data and displayed_teacher_data['level']:
            level_id = displayed_teacher_data['level']
            level_obj = CourseLevel.objects.filter(id=level_id).first()
            displayed_teacher_data['level_name'] = level_obj.name if level_obj else 'N/A'

    context = {
        'teacher_data': displayed_teacher_data,
    }
    return render(request, 'accounts/teacher_register_stage4.html', context)


# --- New View for Application Success Page ---
def application_success_view(request):
    return render(request, 'accounts/application_success.html', {})