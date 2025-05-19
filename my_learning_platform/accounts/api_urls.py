# auth_system/accounts/api_urls.py
from django.urls import path
# Import your API view classes from accounts.api_views
from .api_views import RegisterAPIView, LoginAPIView, LogoutAPIView, UserDetailAPIView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api_register'),
    #path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),
    path('user/', UserDetailAPIView.as_view(), name='api_user_detail'),
    path('login/', csrf_exempt(LoginAPIView.as_view()), name='api_login'),
]