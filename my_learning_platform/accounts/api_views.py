import logging
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import IntegrityError
from django.db.models import Q # For OR conditions in lookups
from django.utils import timezone # For approval/rejection dates

from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token as AuthToken # Renamed to avoid conflict

from .models import CustomUser, Profile, TeacherCourse, CourseCategory, CourseLevel, EnrolledCourse # Import all relevant models
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    DeleteUserByEmailSerializer,
    TeacherRegisterSerializer,   # Specific serializer for teacher registration
    StudentRegisterSerializer,   # Specific serializer for student registration
    ProfileSerializer,           # For viewing/updating user profiles
    TeacherCourseSerializer,     # For teacher-specific course management
    CourseCategorySerializer,    # For listing course categories
    CourseLevelSerializer,       # For listing course levels
    EnrolledCourseSerializer,    # For student's enrolled courses
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Get the CustomUser model
User = get_user_model()


# --- Base Registration View (if you needed a generic one for any user type) ---
# NOTE: You might not use this if you always register via TeacherRegisterAPIView or StudentRegisterAPIView.
# class RegisterAPIView(generics.CreateAPIView):
#     queryset = User.objects.all()
#     serializer_class = UserRegisterSerializer
#     permission_classes = [permissions.AllowAny]


# --- Teacher Registration View ---
class TeacherRegisterAPIView(generics.CreateAPIView):
    """
    API endpoint for registering a new teacher user.
    Uses TeacherRegisterSerializer to handle user and profile creation,
    setting user_type='teacher' and marking application as pending.
    """
    queryset = User.objects.all()
    serializer_class = TeacherRegisterSerializer  # Using the specific teacher serializer
    permission_classes = [permissions.AllowAny]   # Allow anyone to register as a teacher

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # The serializer's create method (in TeacherRegisterSerializer)
        # now handles the creation of CustomUser with user_type='teacher'
        # and its associated Profile with pending status.
        user = serializer.save()

        # Access the profile instance created by the serializer for the response
        profile = user.profile

        logger.info(f"Teacher '{user.username}' (ID: {user.id}) registered. Profile ID: {profile.id}. Pending status: {profile.is_teacher_application_pending}")

        headers = self.get_success_headers(serializer.data)
        return Response({
            "message": "Teacher application submitted successfully and is awaiting approval.",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type, # Should be 'teacher'
            "is_teacher_application_pending": profile.is_teacher_application_pending,
            "profile_id": profile.id,
        }, status=status.HTTP_201_CREATED, headers=headers)


# --- Student Registration View ---
class StudentRegisterAPIView(generics.CreateAPIView):
    """
    API endpoint for registering a new student user.
    Uses StudentRegisterSerializer to handle user and profile creation,
    setting user_type='student'.
    """
    queryset = User.objects.all()
    serializer_class = StudentRegisterSerializer # Using the specific student serializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save() # StudentRegisterSerializer creates CustomUser and Profile

        profile = user.profile # Access the created profile

        logger.info(f"Student '{user.username}' (ID: {user.id}) registered. Profile ID: {profile.id}.")

        headers = self.get_success_headers(serializer.data)
        return Response({
            "message": "Student registration successful.",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type, # Should be 'student'
            "profile_id": profile.id,
        }, status=status.HTTP_201_CREATED, headers=headers)


# --- User Login View ---
class LoginAPIView(APIView):
    """
    API endpoint for user login.
    Supports login with either username or email.
    Returns an authentication token upon successful login.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        logger.info("LoginAPIView POST method reached.")
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True) # Will return 400 if validation fails

        username_or_email = serializer.validated_data['username_or_email']
        password = serializer.validated_data['password']

        user = None
        # Try to authenticate by username first
        user = authenticate(request, username=username_or_email, password=password)

        if user is None:
            # If not found by username, try by email
            try:
                # Case-insensitive email lookup
                user_by_email = User.objects.get(email__iexact=username_or_email)
                user = authenticate(request, username=user_by_email.username, password=password)
            except User.DoesNotExist:
                pass # user remains None if not found by email either

        if user is not None:
            # User is valid, log them in and get/create token
            login(request, user) # This sets the session, useful if SessionAuthentication is also used
            token, created = AuthToken.objects.get_or_create(user=user)
            logger.info(f"User '{user.username}' (ID: {user.id}) logged in successfully.")
            return Response({
                'message': 'Login successful',
                'token': token.key,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
            }, status=status.HTTP_200_OK)
        else:
            # Authentication failed
            logger.warning(f"Failed login attempt for username/email: {username_or_email}")
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


# --- User Logout View ---
class LogoutAPIView(APIView):
    """
    API endpoint for user logout.
    Deletes the user's authentication token, effectively logging them out.
    """
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users can log out

    def post(self, request, *args, **kwargs):
        try:
            # Delete the user's authentication token
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete()
            # Log out the user from the session (if session authentication is active)
            logout(request)
            logger.info(f"User '{request.user.username}' (ID: {request.user.id}) logged out successfully.")
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error during logout for user {request.user.username}: {e}", exc_info=True)
            return Response({'error': f'An error occurred during logout: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- User Profile View (Retrieve and Update Own Profile) ---
class MyProfileAPIView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for authenticated users to retrieve and update their own profile.
    """
    serializer_class = ProfileSerializer # Uses the comprehensive ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensure the user can only access/update their own profile
        return self.request.user.profile

    def perform_update(self, serializer):
        # Optional: Add custom logic before saving profile updates.
        # For example, if certain critical fields change, you might
        # set `is_teacher_application_pending = True` again for teachers.
        profile = serializer.save()
        logger.info(f"Profile for user '{profile.user.username}' (ID: {profile.user.id}) updated.")


# --- Delete User View (Admin Only) ---
class DeleteUserByEmailAPIView(APIView):
    """
    API endpoint for administrators to delete a user by email address.
    Includes checks to prevent deleting superusers without proper privileges
    and preventing an admin from deleting their own account.
    """
    permission_classes = [permissions.IsAdminUser] # Only admins can access
    serializer_class = DeleteUserByEmailSerializer # Serializer for email input validation

    def delete(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']

        logger.info(f"Admin '{request.user.username}' (ID: {request.user.id}) attempting to delete user with email: {email}")

        try:
            user_to_delete = User.objects.get(email__iexact=email) # Case-insensitive email lookup

            # Prevent deletion of superusers by non-superusers
            if user_to_delete.is_superuser and not request.user.is_superuser:
                logger.warning(f"Non-superuser '{request.user.username}' attempted to delete superuser '{email}'.")
                return Response({"detail": "Cannot delete a superuser without superuser privileges."}, status=status.HTTP_403_FORBIDDEN)

            # Prevent admins from deleting their own account via this API
            if user_to_delete == request.user:
                logger.warning(f"Admin '{request.user.username}' attempted to delete their own account.")
                return Response({"detail": "Cannot delete your own account via this API."}, status=status.HTTP_403_FORBIDDEN)

            user_to_delete.delete() # This will trigger CASCADE deletion for the Profile
            logger.info(f"Successfully deleted user with email: {email}")
            return Response({"detail": f"User {email} deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            logger.warning(f"User with email '{email}' not found for deletion attempt by '{request.user.username}'.")
            return Response({"detail": f"User with email {email} not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error deleting user '{email}': {e}", exc_info=True)
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# --- Teacher Course Management Views ---
class TeacherCourseListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for teachers to list their own courses and create new ones.
    Admins can list all courses.
    """
    serializer_class = TeacherCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Teachers see only their own courses
        if self.request.user.user_type == 'teacher':
            return TeacherCourse.objects.filter(teacher_profile=self.request.user.profile)
        # Admins can see all courses
        elif self.request.user.user_type == 'admin':
            return TeacherCourse.objects.all()
        # Other user types (e.g., students) see no courses here
        return TeacherCourse.objects.none()

    def perform_create(self, serializer):
        # Ensure only teachers can create courses and link to their profile
        if self.request.user.user_type == 'teacher':
            serializer.save(teacher_profile=self.request.user.profile)
            logger.info(f"Teacher '{self.request.user.username}' created course '{serializer.instance.title}'.")
        else:
            logger.warning(f"User '{self.request.user.username}' (type: {self.request.user.user_type}) attempted to create a course without teacher role.")
            raise permissions.PermissionDenied("Only teachers can create courses.")


class TeacherCourseDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for teachers to retrieve, update, or delete their specific courses.
    Admins can also perform these actions on any course.
    """
    serializer_class = TeacherCourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = TeacherCourse.objects.all() # Start with all, then filter in get_object

    def get_object(self):
        obj = super().get_object() # Get the course object based on PK from URL

        # Ensure user can only access/update/delete their own courses or if they are an admin
        if obj.teacher_profile.user != self.request.user and self.request.user.user_type != 'admin':
            logger.warning(f"User '{self.request.user.username}' (ID: {self.request.user.id}) attempted unauthorized access to course '{obj.title}' (ID: {obj.id}).")
            raise permissions.PermissionDenied("You do not have permission to access this course.")
        return obj

    def perform_update(self, serializer):
        # Prevent non-admins from changing course status
        if 'status' in serializer.validated_data and self.request.user.user_type != 'admin':
            logger.warning(f"User '{self.request.user.username}' (ID: {self.request.user.id}) attempted unauthorized status change for course '{serializer.instance.title}'.")
            raise permissions.PermissionDenied("You are not authorized to change course status.")

        serializer.save()
        logger.info(f"Course '{serializer.instance.title}' (ID: {serializer.instance.id}) updated by '{self.request.user.username}'.")

    def perform_destroy(self, instance):
        # Ensure only the teacher or an admin can delete a course
        if instance.teacher_profile.user != self.request.user and self.request.user.user_type != 'admin':
            logger.warning(f"User '{self.request.user.username}' (ID: {self.request.user.id}) attempted unauthorized deletion of course '{instance.title}'.")
            raise permissions.PermissionDenied("You do not have permission to delete this course.")
        logger.info(f"Course '{instance.title}' (ID: {instance.id}) deleted by '{self.request.user.username}'.")
        instance.delete()


# --- Public Course Data Views (Accessible to anyone) ---
class CourseCategoryListAPIView(generics.ListAPIView):
    """
    API endpoint to list all available course categories.
    Accessible to any user (authenticated or not).
    """
    serializer_class = CourseCategorySerializer
    queryset = CourseCategory.objects.all()
    permission_classes = [permissions.AllowAny]

class CourseLevelListAPIView(generics.ListAPIView):
    """
    API endpoint to list all available course levels.
    Accessible to any user (authenticated or not).
    """
    serializer_class = CourseLevelSerializer
    queryset = CourseLevel.objects.all()
    permission_classes = [permissions.AllowAny]


# --- Student Enrolled Courses View ---
class MyEnrolledCoursesListAPIView(generics.ListAPIView):
    """
    API endpoint for students to view the courses they are enrolled in.
    """
    serializer_class = EnrolledCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Students should only see their own enrolled courses
        if self.request.user.user_type == 'student':
            logger.info(f"Student '{self.request.user.username}' fetching enrolled courses.")
            return EnrolledCourse.objects.filter(student=self.request.user.profile)
        # Other user types should not access this endpoint
        logger.warning(f"Non-student user '{self.request.user.username}' attempted to access enrolled courses list.")
        return EnrolledCourse.objects.none()


# --- Admin Views for Teacher Application Approval Workflow ---
class TeacherApplicationListAPIView(generics.ListAPIView):
    """
    API endpoint for administrators to list teacher applications that are pending approval.
    """
    serializer_class = ProfileSerializer # Use ProfileSerializer to display application details
    permission_classes = [permissions.IsAdminUser] # Only admins can view this list

    def get_queryset(self):
        logger.info(f"Admin '{self.request.user.username}' fetching pending teacher applications.")
        return Profile.objects.filter(
            user__user_type='teacher',
            is_teacher_application_pending=True,
            is_teacher_approved=False
        )


class TeacherApplicationApproveRejectAPIView(generics.UpdateAPIView):
    """
    API endpoint for administrators to approve or reject a specific teacher application.
    Expected data: {"action": "approve"} or {"action": "reject", "rejection_reason": "..."}
    """
    serializer_class = ProfileSerializer # Using ProfileSerializer for context, but custom update logic
    permission_classes = [permissions.IsAdminUser]
    queryset = Profile.objects.filter(user__user_type='teacher') # Filter for teacher profiles

    def update(self, request, *args, **kwargs):
        profile = self.get_object()
        action = request.data.get('action')
        reason = request.data.get('rejection_reason', None)

        if action == 'approve':
            if profile.is_teacher_approved:
                return Response({"detail": "Teacher application is already approved."}, status=status.HTTP_400_BAD_REQUEST)
            if not profile.is_teacher_application_pending:
                 return Response({"detail": "Teacher application is not in pending state."}, status=status.HTTP_400_BAD_REQUEST)

            profile.is_teacher_application_pending = False
            profile.is_teacher_approved = True
            profile.approved_by = request.user
            profile.approval_date = timezone.now()
            profile.rejected_by = None
            profile.rejection_date = None
            profile.rejection_reason = None
            profile.save()
            logger.info(f"Teacher '{profile.user.username}' (ID: {profile.user.id}) application APPROVED by admin '{request.user.username}'.")
            return Response({"message": "Teacher application approved successfully."}, status=status.HTTP_200_OK)

        elif action == 'reject':
            if profile.is_teacher_approved:
                return Response({"detail": "Approved teacher cannot be directly rejected. Revoke approval first if needed."}, status=status.HTTP_400_BAD_REQUEST)
            if not profile.is_teacher_application_pending and not profile.rejected_by:
                # Allow re-rejection if it was pending and rejected earlier
                 pass
            if not reason:
                return Response({"detail": "Rejection reason is required when rejecting."}, status=status.HTTP_400_BAD_REQUEST)

            profile.is_teacher_application_pending = False
            profile.is_teacher_approved = False
            profile.rejected_by = request.user
            profile.rejection_date = timezone.now()
            profile.rejection_reason = reason
            profile.approved_by = None
            profile.approval_date = None
            profile.save()
            logger.info(f"Teacher '{profile.user.username}' (ID: {profile.user.id}) application REJECTED by admin '{request.user.username}'. Reason: '{reason}'")
            return Response({"message": "Teacher application rejected successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid action. Must be 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)
class TeacherCourseReportAPIView(generics.ListAPIView):
    """
    API endpoint to retrieve all courses for a specific teacher (by profile ID).
    Accessible by admins and the teacher themselves.
    """
    serializer_class = TeacherCourseSerializer
    permission_classes = [permissions.IsAuthenticated] # Requires authentication

    def get_queryset(self):
        teacher_profile_id = self.kwargs['pk'] # Get the teacher's profile ID from the URL

        try:
            # First, check if the requested profile ID belongs to a teacher
            teacher_profile = Profile.objects.get(id=teacher_profile_id, user__user_type='teacher')
        except Profile.DoesNotExist:
            logger.warning(f"Teacher profile with ID {teacher_profile_id} not found or is not a teacher.")
            raise status.HTTP_404_NOT_FOUND # Or raise a custom exception for better error handling

        # Permission check:
        # 1. If the requesting user is an admin, they can see any teacher's report.
        # 2. If the requesting user is the teacher whose report is being requested.
        if self.request.user.user_type == 'admin' or self.request.user.profile == teacher_profile:
            logger.info(f"User '{self.request.user.username}' (type: {self.request.user.user_type}) accessing courses for teacher profile ID: {teacher_profile_id}")
            return TeacherCourse.objects.filter(teacher_profile=teacher_profile)
        else:
            logger.warning(f"User '{self.request.user.username}' (ID: {self.request.user.id}) attempted unauthorized access to teacher report for profile ID: {teacher_profile_id}.")
            raise permissions.PermissionDenied("You do not have permission to access this teacher's report.")
