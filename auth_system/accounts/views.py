# auth_system/accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages.storage import default_storage
from .forms import SignupForm, CustomUserChangeForm, ProfileForm
from .models import Profile # Import Profile model if not already imported


# --- Core Landing Page View ---
def portfolio_view(request):
    context = {}
    return render(request, 'index.html', context)

# --- CV Page View ---
def cv_view(request):
    context = {}
    return render(request, 'cv.html', context)

# --- Portfolio Page View ---
def portfolio_page_view(request):
    context = {}
    return render(request, 'portfolio_page.html', context)

# --- Certificates Page View ---
def certificates_view(request):
    context = {}
    return render(request, 'certificates.html', context)

# --- NEW Course Page View ---
# This view will handle the /courses/ URL
def course_view(request):
    print("\n--- Course View Accessed ---") # Debug print
    context = {
        # Add context data specific to the courses page here
        'page_title': 'My Courses & Learning'
    }
    # Render the new courses.html template
    return render(request, 'courses.html', context)


# --- Contact Page View ---
def contact_view(request):
    context = {}
    return render(request, 'contact.html', context)

# --- About Page View ---
def about_view(request):
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
                return redirect('dashboard')
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
    return redirect('portfolio')


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


        print("Preparing context for render.")
        print(f"user_form defined before context: { 'user_form' in locals() }")
        print(f"profile_form defined before context: { 'profile_form' in locals() }")


        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }
        print("Rendering template.")
        return render(request, 'profile.html', context)
