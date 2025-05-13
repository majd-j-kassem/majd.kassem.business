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
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials")
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('login')

# Add the dashboard view here if you moved it from auth_system/urls.py
@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')

# --- END of Web View Functions ---