import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__) # Basic logger for better output

class Command(BaseCommand):
    help = 'Creates a superuser if one does not already exist using environment variables for credentials.'

    def handle(self, *args, **options):
        User = get_user_model()

        # Retrieve credentials from environment variables
        # Using .get() for safety; None will be returned if not set
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        # Basic validation for environment variables
        if not username:
            self.stderr.write(self.style.ERROR(
                "Error: DJANGO_SUPERUSER_USERNAME environment variable not set. Superuser creation skipped."
            ))
            return
        if not email:
            self.stderr.write(self.style.ERROR(
                "Error: DJANGO_SUPERUSER_EMAIL environment variable not set. Superuser creation skipped."
            ))
            return
        if not password:
            self.stderr.write(self.style.ERROR(
                "Error: DJANGO_SUPERUSER_PASSWORD environment variable not set. Superuser creation skipped."
            ))
            return

        # Check if a superuser with this username already exists
        if not User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'Attempting to create superuser: {username}'))
            try:
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS('Superuser created successfully.'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error creating superuser: {e}'))
                # Consider adding more specific error handling here if needed
        else:
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists. Skipping creation.'))