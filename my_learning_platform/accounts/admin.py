from django.contrib import admin

# Register your models here.
# auth_system/accounts/admin.py

from django.contrib import admin
# Make sure to import all your new models here
from .models import CustomUser, Profile, CourseCategory, CourseLevel, TeacherCourse

# ... (Keep all your existing admin registrations, e.g., for CustomUser, Profile) ...

# Register your new models
admin.site.register(CourseCategory)
admin.site.register(CourseLevel)
admin.site.register(TeacherCourse)