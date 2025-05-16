from django.contrib import admin
from django.urls import path, include

# IMPORTANT: Ensure all these views are defined as functions in your accounts/views.py file.
# If any are missing, create empty placeholder functions for them.
from accounts.views import (
    portfolio_view,
    cv_view,
    portfolio_page_view,
    certificates_view, #  This is now correctly named
    contact_view,
    about_view,
    login_view,
    dashboard,
    logout_view,
    signup_view,  # <--- Ensure this is imported
)

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- CORE LANDING PAGE & NAVIGATION URLS ---
    path('', portfolio_view, name='portfolio'),

    # Maps for your main navigation menu items
    path('cv/', cv_view, name='cv'),
    path('portfolio/', portfolio_page_view, name='portfolio_page'),
    path('certificates/', certificates_view, name='certificates'),
    path('contact/', contact_view, name='contact'),
    path('about/', about_view, name='about'),
    path('courses/', certificates_view, name='courses'),
    # --- ACCOUNT-RELATED URLS ---
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('signup/', signup_view, name='signup'),  # <---  Make SURE this line EXISTS and is CORRECT

    # IMPORTANT:  If you have an accounts/urls.py, remove *conflicting* entries from it.
    # If it contains *only* API URLs, keep it.
    # If it has login/logout/signup, *remove those from that file*.
    # path('accounts/', include('accounts.urls')),  #  Comment out this line if it's causing conflicts

    # --- API DOCUMENTATION URLS ---
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # --- MAIN API URLS ---
    path('api/', include('accounts.api_urls')),  #  Keep this if it contains API URLs
]