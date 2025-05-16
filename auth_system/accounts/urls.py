#auth_system/accounts/urls.py
from django.urls import path
# Import your web view functions from accounts.views
from .views import signup_view, login_view, logout_view, dashboard, courses # Make sure dashboard is imported here

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'), # Include the dashboard path
    path('courses/', courses, name='courses'), 
]