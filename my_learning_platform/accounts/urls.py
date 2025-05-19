# accounts/urls.py (APP-LEVEL URLS for your 'accounts' app)
from django.urls import path
from . import views # This import is CORRECT here because views.py is in the same 'accounts' app directory

urlpatterns = [
    # Core Landing Page (your homepage)

    # Main Navigation Menu Items
    path('cv/', views.cv_view, name='cv'),
    path('portfolio/', views.portfolio_page_view, name='portfolio_page'),
    path('certificates/', views.certificates_view, name='certificates'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('courses/', views.course_view, name='courses'),
    path('', views.index_view, name='index'),
    # Authentication & User Management URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Optional: If 'courses' was just an alias for 'certificates', you can remove it.
    # If you still want it, keep it here:
    # path('courses/', views.certificates_view, name='courses'),
]