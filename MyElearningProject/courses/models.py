# courses/models.py

from django.db import models
from django.contrib.auth import get_user_model # If you want to link courses to creators/teachers

User = get_user_model() # Get the currently active User model

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200, help_text="A unique slug for SEO and URL purposes.")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_hours = models.IntegerField(help_text="Total duration of the course in hours (e.g., 40 for 40 hours).")
    image = models.ImageField(upload_to='course_images/', blank=True, null=True, help_text="Upload a cover image for the course.")
    category = models.CharField(max_length=100, blank=True, default="Programming", help_text="e.g., 'Web Development', 'Data Science'")
    level = models.CharField(max_length=50, choices=[
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ], default='Beginner', help_text="Difficulty level of the course.")
    is_published = models.BooleanField(default=False, help_text="Check to make the course visible on the public site.")

    # Optional: Link to the user who created/owns the course if needed
    # creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_courses')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title']
        verbose_name = "Course"
        verbose_name_plural = "Courses"