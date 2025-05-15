from django.contrib import admin
from django.urls import path, include
from accounts import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', views.login_view, name='home'),

    # OpenAPI schema endpoint (define before including API URLs)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI endpoint (define before including API URLs)
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Your main API URLs
    path('api/', include('accounts.api_urls')),
]