# auth_system/accounts/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal # Ensure Decimal is imported for price/commission fields

from .models import Profile, CourseCategory, CourseLevel, TeacherCourse, EnrolledCourse # Import relevant models

User = get_user_model() # This will now be your CustomUser

# --- Base User Registration Serializer (for core CustomUser fields) ---
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True) # Email is required for registration

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email address is already in use.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        # user_type will be set by specific serializers (Teacher/Student)
        user = User.objects.create_user(**validated_data)
        return user

# --- Teacher Registration Serializer ---
class TeacherRegisterSerializer(UserRegisterSerializer):
    # Profile fields specific to teacher application
    qualifications = serializers.CharField(required=False, allow_blank=True, source='profile.qualifications')
    experience_years = serializers.IntegerField(required=False, default=0, source='profile.experience_years')
    university = serializers.CharField(required=False, allow_blank=True, source='profile.university')
    graduation_year = serializers.IntegerField(required=False, source='profile.graduation_year')
    major = serializers.CharField(required=False, allow_blank=True, source='profile.major')
    # Add other teacher-specific profile fields as needed here

    class Meta(UserRegisterSerializer.Meta):
        fields = UserRegisterSerializer.Meta.fields + (
            'qualifications', 'experience_years', 'university',
            'graduation_year', 'major',
            # Add other teacher profile fields here
        )

    def create(self, validated_data):
        # Extract profile data using the 'source' mapping
        profile_data = {
            'qualifications': validated_data.pop('profile', {}).get('qualifications', ''),
            'experience_years': validated_data.pop('profile', {}).get('experience_years', 0),
            'university': validated_data.pop('profile', {}).get('university', ''),
            'graduation_year': validated_data.pop('profile', {}).get('graduation_year', None),
            'major': validated_data.pop('profile', {}).get('major', ''),
            # Ensure other profile fields from the serializer are extracted
            # You might need to adjust how these are popped based on the 'source' attribute
            # For simplicity, if source='profile.field_name', they will be nested under 'profile' in validated_data
            # We will handle these explicitly below
        }

        # The 'source' attribute on fields like 'profile.qualifications'
        # causes DRF to nest the data under a 'profile' dictionary in `validated_data`.
        # So, we need to extract those nested fields.
        profile_fields_from_validated_data = validated_data.pop('profile', {})


        with transaction.atomic():
            # Create the CustomUser with user_type='teacher'
            validated_data['user_type'] = 'teacher'
            user = super().create(validated_data) # Calls UserRegisterSerializer's create

            # Create or update the Profile linked to the new user
            # Combine direct profile fields with those extracted via 'source'
            Profile.objects.create(
                user=user,
                # Default values for fields not provided by the teacher registration,
                # or those that are typically set by the system/later.
                # All 'source' fields will be in profile_fields_from_validated_data
                **profile_fields_from_validated_data,
                is_teacher_application_pending=True, # Automatically set for new teacher registrations
                is_teacher_approved=False # Not approved by default
            )
            return user


# --- Student Registration Serializer ---
class StudentRegisterSerializer(UserRegisterSerializer):
    # Student-specific profile fields (if any, from your Profile model)
    # E.g., if you had a 'grade_level' field on Profile that students use:
    # grade_level = serializers.CharField(required=False, allow_blank=True, source='profile.grade_level')

    class Meta(UserRegisterSerializer.Meta):
        fields = UserRegisterSerializer.Meta.fields + (
            # Add student-specific profile fields here if they exist
            # e.g., 'grade_level',
        )

    def create(self, validated_data):
        # Extract student profile specific data if any, similar to teacher serializer
        profile_fields_from_validated_data = validated_data.pop('profile', {})

        with transaction.atomic():
            # Create the CustomUser with user_type='student'
            validated_data['user_type'] = 'student'
            user = super().create(validated_data)

            # Create the Profile linked to the new user
            Profile.objects.create(
                user=user,
                **profile_fields_from_validated_data # Pass any student-specific profile fields
            )
            return user

# --- User Login Serializer ---
class UserLoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField()
    password = serializers.CharField(write_only=True)

# --- Delete User Serializer ---
class DeleteUserByEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

# --- Profile Serializer (for viewing/updating existing profiles) ---
class ProfileSerializer(serializers.ModelSerializer):
    # Use source to map profile fields to the user's direct access
    # These fields will be available directly at the top level of the JSON
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)

    class Meta:
        model = Profile
        # Include all relevant fields from the Profile model
        fields = (
            'username', 'email', 'user_type', 'profile_picture', 'bio',
            'full_name_en', 'full_name_ar', 'phone_number',
            'experience_years', 'university', 'graduation_year', 'major',
            'is_teacher_application_pending', 'is_teacher_approved',
            'commission_percentage', # This should typically be read-only or only editable by admins
            # Add other fields you want to expose or allow updating
        )
        read_only_fields = (
            'is_teacher_application_pending', 'is_teacher_approved',
            'commission_percentage', # Only admins should set commission
        )
        # You might also want to explicitly add read_only=True for approval/rejection fields
        # if they are only managed by admins

    def update(self, instance, validated_data):
        # Handle updating fields in the Profile model
        # For fields with 'source', data comes nested from the request,
        # but is applied directly to the instance by the serializer.
        return super().update(instance, validated_data)


# --- Course Serializers ---

class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = '__all__'

class CourseLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseLevel
        fields = '__all__'

class TeacherCourseSerializer(serializers.ModelSerializer):
    # Display related data using their serializers
    categories = CourseCategorySerializer(many=True, read_only=True)
    level = CourseLevelSerializer(read_only=True)

    # For creating/updating, you might want to send category/level IDs
    category_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=CourseCategory.objects.all(), write_only=True, source='categories'
    )
    level_id = serializers.PrimaryKeyRelatedField(
        queryset=CourseLevel.objects.all(), write_only=True, source='level'
    )

    class Meta:
        model = TeacherCourse
        fields = (
            'id', 'title', 'description', 'course_picture', 'video_trailer_url', 'price',
            'language', 'categories', 'level', 'featured', 'status',
            'created_at', 'updated_at',
            'category_ids', 'level_id' # Include these for write operations
        )
        read_only_fields = ('teacher_profile', 'status', 'created_at', 'updated_at') # Teacher profile is set in view

    # You might want to override create/update if you need custom logic
    # For example, to ensure the teacher_profile is set correctly in the view.
    def create(self, validated_data):
        # `categories` is now handled by `category_ids` due to source
        # `level` is handled by `level_id` due to source
        categories_data = validated_data.pop('categories', [])
        level_data = validated_data.pop('level', None)

        course = TeacherCourse.objects.create(**validated_data)
        if categories_data:
            course.categories.set(categories_data)
        if level_data:
            course.level = level_data
            course.save() # Save the course again if level is updated separately

        return course

    def update(self, instance, validated_data):
        categories_data = validated_data.pop('categories', None)
        level_data = validated_data.pop('level', None)

        instance = super().update(instance, validated_data)

        if categories_data is not None:
            instance.categories.set(categories_data)
        if level_data is not None:
            instance.level = level_data
            instance.save()

        return instance


class EnrolledCourseSerializer(serializers.ModelSerializer):
    # Display full course and student details for readability
    student = serializers.CharField(source='student.user.username', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    course_teacher = serializers.CharField(source='course.teacher_profile.user.username', read_only=True)


    class Meta:
        model = EnrolledCourse
        fields = ('id', 'student', 'course', 'course_title', 'course_teacher', 'enrolled_at', 'fee_paid')
        read_only_fields = ('student', 'enrolled_at', 'fee_paid') # student is set automatically, fee_paid might be from payment gateway

    # You'll likely create EnrolledCourse instances in a view after a successful payment
    # or direct enrollment logic, not directly via this serializer's create method.