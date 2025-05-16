from django.contrib import admin
from django.urls import path, include

# IMPORTANT: Ensure all these views are defined as functions in your accounts/views.py file.
# If any are missing, create empty placeholder functions for them.
from accounts.views import (
    portfolio_view,      # Handles your main landing page (index.html)
    cv_view,             # Handles your CV page (cv.html)
    portfolio_page_view, # Handles your dedicated portfolio page (portfolio_page.html)
    certificates_view,        # Handles your courses page (courses.html)
    contact_view,        # Handles your new contact page (contact.html)
    about_view,          # Handles your new about page (about.html)
    login_view,          # Your existing login view
    dashboard,            # Your existing dashboard view
    logout_view
)

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- CORE LANDING PAGE & NAVIGATION URLS ---
    # This maps the root URL ('/') to your portfolio_view and names it 'portfolio'.
    # This is CRITICAL for your 'Home' link in templates.
    path('', portfolio_view, name='portfolio'), 

    # Maps for your main navigation menu items
    path('cv/', cv_view, name='cv'),
    path('portfolio/', portfolio_page_view, name='portfolio_page'), # A distinct 'portfolio' for project listings
    path('certificates/', certificates_view, name='certificates'),
    path('contact/', contact_view, name='contact'),
    path('about/', about_view, name='about'),

    # --- ACCOUNT-RELATED URLS ---
    # This maps your login page to /login/ and names it 'login'.
    path('login/', login_view, name='login'), 
     path('logout/', logout_view, name='logout'), 
    # Includes other URLs from your accounts app (e.g., dashboard, signup, logout if defined there)
    path('accounts/', include('accounts.urls')), 

    # --- API DOCUMENTATION URLS ---
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # --- MAIN API URLS ---
    path('api/', include('accounts.api_urls')),
]