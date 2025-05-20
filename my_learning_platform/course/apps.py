from django.apps import AppConfig

class CourseConfig(AppConfig):
    name = 'course'
    label = 'courses'  # Changed to be more unique
    verbose_name = "Course Management"