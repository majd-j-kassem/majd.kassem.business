"""
Django settings for auth_system project.
"""

from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
if os.path.exists(BASE_DIR / '.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / '.env')
    except ImportError:
        pass

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'a-default-secret-key-for-development-only-replace-this-in-prod')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS_STRING = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STRING.split(',') if host.strip()]

# Application definition
INSTALLED_APPS = [
     'jazzmin', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'course.apps.CourseConfig',
    'accounts.apps.AccountsConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
]
AUTH_USER_MODEL = 'accounts.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'auth_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'auth_system.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/' # Keep only one of these lines

STATICFILES_DIRS = [
    BASE_DIR / 'static', # Updated to use Path object with / operator
]

# This is the ABSOLUTE path to the directory where collectstatic will collect all static files for deployment.
STATIC_ROOT = BASE_DIR / 'staticfiles' # UNCOMMENTED and using Path object

# Media files
MEDIA_ROOT = BASE_DIR / 'media' # Also update this for consistency
MEDIA_URL = '/media/'
# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly'
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Your API Documentation',
    'DESCRIPTION': 'API description',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Redirect URLs
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'portfolio'

# Custom User Model

# Production-specific security settings (example - adjust as needed)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # Uncomment if behind a proxy

# CORS/CSRF origins (example - adjust if using a separate frontend)
# CORS_ALLOWED_ORIGINS = [
#    "http://localhost:3000",
#    "https://your-frontend-domain.com",
# ]
# CSRF_TRUSTED_ORIGINS = [
#     "http://localhost:3000",
#     "https://your-frontend-domain.com",
# ]
JAZZMIN_SETTINGS = {
    # title of the window (Will default to current_admin_site.site_title if absent or None)
    "site_title": "My Learning Platform Admin",

    # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
    "site_header": "Learning Platform",

    # square logo to use for your site, must be a static file
    "site_logo": "admin/img/logo.png", # You can replace this with your own logo later

    # Welcome text
    "welcome_sign": "Welcome to the Learning Platform Admin!",

    # Copyright on the footer
    "copyright": "Majd Kassem Business",

    # The model admin to search from the search bar, search bar omitted if excluded
    "search_model": ["accounts.CustomUser", "accounts.Profile", "accounts.TeacherCourse"],

    # Field name on user model that contains name for display in the template
    "user_avatar": None, # Set to 'profile.profile_picture' if you link user's profile pic to their admin icon

    #############
    # UI Tweaks #
    #############
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [], # List apps to hide e.g., ["auth", "authtoken"]
    "hide_models": [], # List models to hide e.g., ["auth.group", "auth.permission"]

    # Custom links to include in the sidebar (top level)
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Website", "url": "admin:index", "url": "/", "new_window": True}, # Link to your main site
        {"model": "auth.User"}, # Link to User model
        {"app": "accounts"}, # Link to accounts app
    ],
}