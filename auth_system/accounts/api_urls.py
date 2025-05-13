# auth_system/accounts/api_urls.py
from django.urls import path
# Import your API view classes from accounts.api_views
from .api_views import RegisterAPIView, LoginAPIView, LogoutAPIView, UserDetailAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api_register'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('user/', UserDetailAPIView.as_view(), name='api_user_detail'),
]