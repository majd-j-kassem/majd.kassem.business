# auth_system/accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.messages.storage import default_storage
from django.core.mail import send_mail # Import send_mail
from django.conf import settings # Import settings

from .forms import SignupForm, CustomUserChangeForm, ProfileForm, ContactForm # Import ContactForm
from .models import Profile # Import Profile model if not already imported


# --- Core Homepage View ---
def index_view(request):
    print("\n--- Index View Accessed (Homepage) ---") # Debug print
    context = {
        # You can add context data here if your homepage needs it
        'page_title': 'Welcome to My Portfolio'
    }
    return render(request, 'index.html', context)


# --- CV Page View ---
def cv_view(request):
    print("\n--- CV View Accessed ---") # Debug print
    context = {}
    return render(request, 'cv.html', context)

# --- Portfolio Page View ---
def portfolio_page_view(request):
    print("\n--- Portfolio Page View Accessed ---") # Debug print
    context = {}
    return render(request, 'portfolio_page.html', context)

# --- Certificates Page View ---
def certificates_view(request):
    print("\n--- Certificates View Accessed ---") # Debug print
    context = {}
    return render(request, 'certificates.html', context)

# --- Course Page View ---
# This view renders the courses.html template
def course_view(request):
    print("\n--- Course View Accessed ---") # Debug print
    # You might want to require login for this page
    # from django.contrib.auth.decorators import login_required
    # @login_required
    context = {
        'page_title': 'My Courses & Learning' # Example context data
    }
    return render(request, 'courses.html', context)


# --- Contact Page View (Updated to handle form) ---
def contact_view(request):
    print(f"\n--- Contact View Accessed (Method: {request.method}) ---")
    if request.method == 'POST':
        form = ContactForm(request.POST)
        print("Contact form instantiated with POST data.")
        if form.is_valid():
            print("Contact form is valid. Processing message...")
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone'] # This will be None if not provided and field is not required
            message_content = form.cleaned_data['message']

            # --- Email Sending Logic (Example) ---
            # You would configure your email settings in settings.py
            # For now, this is a placeholder.
            try:
                subject = f'New Contact from Portfolio Site: {name}'
                # Include phone number in the body only if provided
                body = f'Name: {name}\nEmail: {email}\n'
                if phone:
                    body += f'Phone: {phone}\n'
                body += f'\nMessage:\n{message_content}'

                from_email = settings.DEFAULT_FROM_EMAIL # Defined in settings.py
                # Define CONTACT_EMAIL in your settings.py (e.g., CONTACT_EMAIL = 'your.receiving.email@example.com')
                to_email = [settings.CONTACT_EMAIL]

                # Uncomment the line below to actually send the email
                # send_mail(subject, body, from_email, to_email, fail_silently=False)
                print("Email sending logic executed (send_mail commented out).")

                messages.success(request, 'Your message has been sent successfully!')
                print("Contact message processed. Redirecting to contact page...")
                return redirect('contact') # Redirect back to the contact page to show success message and clear form

            except Exception as e:
                print(f"Error processing contact message (or sending email): {e}")
                messages.error(request, 'There was an error sending your message. Please try again later.')
                # Stay on the page with the form and errors

        else:
            print("Contact form is NOT valid.")
            messages.error(request, 'Please correct the errors below.')
            # Stay on the page with the form and errors

    else: # GET request
        form = ContactForm()
        print("Contact form instantiated for GET.")

    context = {
        'form': form, # Pass the form instance to the template
    }
    return render(request, 'contact.html', context)


# --- About Page View ---
def about_view(request):
    print("\n--- About View Accessed ---") # Debug print
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
            # You might want to redirect to 'courses' here as well if that's the desired post-signup landing
            return redirect('dashboard') # Consider changing to 'courses' if needed
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


# --- Login View (Updated to redirect to courses) ---
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
                # --- CHANGE MADE HERE ---
                return redirect('courses') # Redirect to the courses page after successful login
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
    return redirect('index') # Redirect to the homepage named 'index'


# --- Dashboard View ---
# You might not need a separate dashboard if courses is the main logged-in page
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
