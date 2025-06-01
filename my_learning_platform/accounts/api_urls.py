# auth_system/accounts/api_urls.py (Corrected)

from django.urls import path
from .api_views import ( # Renamed from api_views to views for clarity, but use your actual file name
    LoginAPIView,
    LogoutAPIView,
    MyProfileAPIView, # Renamed UserDetailAPIView to MyProfileAPIView as per updated views
    DeleteUserByEmailAPIView,
    TeacherRegisterAPIView,
    StudentRegisterAPIView, # <-- Make sure this is also imported if you have it
    TeacherCourseListCreateAPIView,
    TeacherCourseDetailAPIView,
    CourseCategoryListAPIView,
    CourseLevelListAPIView,
    MyEnrolledCoursesListAPIView,
    TeacherApplicationListAPIView,
    TeacherApplicationApproveRejectAPIView,
    TeacherCourseReportAPIView,
)

urlpatterns = [
    # Authentication
    path('register/teacher/', TeacherRegisterAPIView.as_view(), name='api_register_teacher'),
    path('register/student/', StudentRegisterAPIView.as_view(), name='api_register_student'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('logout/', LogoutAPIView.as_view(), name='api_logout'),

    # User Profile (Self-management)
    path('me/profile/', MyProfileAPIView.as_view(), name='api_my_profile'),

    # Admin - User Management
    path('delete-user/', DeleteUserByEmailAPIView.as_view(), name='api_delete_user'), # Admin only

    # Teacher Course Management
    path('courses/', TeacherCourseListCreateAPIView.as_view(), name='api_teacher_course_list_create'),
    path('courses/<int:pk>/', TeacherCourseDetailAPIView.as_view(), name='api_teacher_course_detail'),

    # Public Course Data (Categories & Levels)
    path('categories/', CourseCategoryListAPIView.as_view(), name='api_course_categories'),
    path('levels/', CourseLevelListAPIView.as_view(), name='api_course_levels'),

    # Student Enrolled Courses
    path('my-enrollments/', MyEnrolledCoursesListAPIView.as_view(), name='api_my_enrollments'),

    # Admin - Teacher Application Workflow
    path('admin/teacher-applications/', TeacherApplicationListAPIView.as_view(), name='api_admin_teacher_applications'),
    path('admin/teacher-applications/<int:pk>/status/', TeacherApplicationApproveRejectAPIView.as_view(), name='api_admin_teacher_application_status'),
    path('teachers/<int:pk>/courses/', TeacherCourseReportAPIView.as_view(), name='api_teacher_course_report'),
]