# auth_system/accounts/views.py (Cleaned up version)

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate # Keep this line
from django.contrib.auth.decorators import login_required # Add this if you're moving dashboard here
from .forms import SignupForm
from django.contrib import messages
# If you need to access the User model directly, use get_user_model()
from django.contrib.auth import get_user_model # Keep or add this if needed in views

# --- Your Web View Functions ---
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Signup successful!")
            return redirect('dashboard')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        # Safely get username and password from POST data
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # You can add a success message
            messages.success(request, f"Welcome back, {username}!")
            # Redirect to the dashboard or home page after successful login
            return redirect('dashboard') # Or 'portfolio' if you prefer

        else:
            # Add an error message for invalid credentials
            messages.error(request, "Invalid username or password.")
            return render(request, 'accounts/login.html', {}) # Render the login page again with error
    else:
        # For a GET request, just render the empty login form
        return render(request, 'accounts/login.html', {})

def dashboard(request):
    if request.user.is_authenticated:
        return render(request, 'accounts/dashboard.html', {})
    else:
        messages.info(request, "Please log in to view the dashboard.")
        return redirect('login') # Redirect to login if not authenticated
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('portfolio') # Redirect to the home page after logout

# ... (other view functions like portfolio_page_view, certificates_view, contact_view, about_view)

# Add the dashboard view here if you moved it from auth_system/urls.py
@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')
# Your existing views
def portfolio_view(request):
    return render(request, 'index.html', {})

def cv_view(request):
    return render(request, 'cv.html', {})

def portfolio_page_view(request):
    return render(request, 'portfolio_page.html', {})

def certificates_view(request): # Renamed function
    return render(request, 'certificates.html', {}) 
# New views for your navigation
def contact_view(request):
    return render(request, 'contact.html', {}) # You will create contact.html

def about_view(request):
    return render(request, 'about.html', {})   # You will create about.html

# --- END of Web View Functions ---