# accounts/urls.py (APP-LEVEL URLS for your 'accounts' app)
from django.urls import path
from . import views # This import is CORRECT here because views.py is in the same 'accounts' app directory

urlpatterns = [
    # Core Landing Page (your homepage)

    # Main Navigation Menu Items
    path('cv/', views.cv_view, name='cv'),
    path('portfolio/', views.portfolio_page_view, name='portfolio_page'),
    path('certificates/', views.certificates_view, name='certificates'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('courses/', views.course_view, name='courses'),
    path('', views.index_view, name='index'),
    # Authentication & User Management URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('teacher_dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('teacher/register/', views.teacher_register_wizard, name='teacher_register_stage1'),
    path('teacher/register/stage2/', views.teacher_register_stage2, name='teacher_register_stage2'),
    #path('teacher/register/stage3/', views.teacher_register_stage3, name='teacher_register_stage3'),
    path('teacher/register/stage4/', views.teacher_register_confirm, name='teacher_register_stage4'),
    path('teacher/register/confirm/', views.teacher_register_confirm, name='teacher_register_confirm'),
    path('teacher/register/password-setting/', views.teacher_register_password_setting, name='teacher_register_password_setting'),
    path('teacher/register/success/', views.application_success_view, name='application_success'),
    # --- Teacher Specific URLs ---
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/courses/add/', views.add_teacher_course, name='add_teacher_course'),
    path('profile/', views.profile_view, name='profile'),
    # Optional: If 'courses' was just an alias for 'certificates', you can remove it.
    # If you still want it, keep it here:
    # path('courses/', views.certificates_view, name='courses'),
]