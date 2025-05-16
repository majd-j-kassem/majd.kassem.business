# auth_system/auth_system/urls.py (PROJECT-LEVEL URLS)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings 
from django.conf.urls.static import static 

# API Documentation URLs (These are typically kept in the project's urls.py)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Include all URL patterns from your 'accounts' app
    # This single line will now handle all your main navigation,
    # authentication, and profile URLs defined within 'accounts/urls.py'.
    path('', include('accounts.urls')),

    # API Documentation URLs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Main API URLs (Keep this if 'accounts.api_urls' defines your REST API endpoints)
    path('api/', include('accounts.api_urls')),
    

]
if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)