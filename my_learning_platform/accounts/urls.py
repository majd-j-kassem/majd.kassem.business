# auth_system/accounts/urls.py (APP-LEVEL URLS for your 'accounts' app)

from django.urls import path
from . import views # This import is CORRECT here because views.py is in the same 'accounts' app directory
from django.contrib.auth import views as auth_views
urlpatterns = [
    # Core Landing Page (your homepage)
    path('', views.index_view, name='index'), # Typically your main site homepage

    # Main Navigation Menu Items
    path('cv/', views.cv_view, name='cv'),
    path('portfolio/', views.portfolio_page_view, name='portfolio_page'),
    path('certificates/', views.certificates_view, name='certificates'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('courses/', views.course_list_view, name='courses'), # The courses list page
    path('course/<int:course_id>/', views.course_detail, name='course_detail'), # Add this too for individual course view
    # Authentication & User Management URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'), # Student/General User Dashboard
    path('profile/edit/', views.profile_edit, name='profile_edit'), # User Profile Edit
    path('register/<int:course_id>/', views.register_for_course, name='register_for_course'),
     # Add course-related URLs here:
    path('courses/', views.course_list_view, name='course_view'), # For your "Back to All Courses" link
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/register/<int:course_id>/', views.register_for_course, name='register_for_course'),
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
    # Teacher Registration Wizard URLs
    path('teacher/register/', views.teacher_register_wizard, name='teacher_register_stage1'),
    path('teacher/register/stage2/', views.teacher_register_stage2, name='teacher_register_stage2'),
    # path('teacher/register/stage3/', views.teacher_register_stage3, name='teacher_register_stage3'), # This was commented out in views.py
    path('teacher/register/confirm/', views.teacher_register_confirm, name='teacher_register_confirm'),
    path('teacher/register/password-setting/', views.teacher_register_password_setting, name='teacher_register_password_setting'),
    path('teacher/register/success/', views.application_success_view, name='application_success'),

    # Teacher Specific URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'), # Teacher's Dashboard
    path('teacher/courses/add/', views.add_teacher_course, name='add_teacher_course'), # Add New Course
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
     # NEW: Teacher Reporting URLs
    path('teacher/reports/summary/', views.teacher_course_reports, name='teacher_course_reports'),
    path('teacher/reports/course/<int:course_id>/', views.teacher_single_course_report, name='teacher_single_course_report'),
    path('teacher/edit-course/<int:course_id>/', views.edit_teacher_course, name='edit_teacher_course'), # NEW
    # Note: Removed duplicate entries for 'teacher_dashboard' and 'add_teacher_course'.
    # Ensure all names ('name=...') are unique across all URLs if you plan to use reverse lookups.
    
    path('profile/update/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
]
