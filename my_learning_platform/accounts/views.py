# auth_system/accounts/views.py

import secrets
import string
import logging
from .forms import ProfileForm
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import IntegrityError
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, F
from decimal import Decimal # Import Decimal from the decimal module
from decimal import Decimal
# --- Consolidated Model Imports ---
from .models import CustomUser, Profile, TeacherCourse, CourseCategory, CourseLevel, EnrolledCourse, AllowedCard
from .models import ContactMessage
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView # This should already be there if you're using UpdateView
# ... other imports (e.g., render, redirect, forms, models)
from django.http import HttpResponse

# --- Consolidated Form Imports ---
from .forms import (
    SignupForm, CustomUserChangeForm, ProfileForm, ContactForm,
    TeacherPersonalInfoForm, TeacherProfessionalDetailsForm,
    TeacherCourseForm,
    PaymentForm,
    PasswordSettingForm
)

User = get_user_model()

def generate_random_password(length=12):
    """Generate a secure random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))

# --- Helper Function: Check if user is an approved teacher ---
def is_approved_teacher(user):
    """
    Test to check if the user is a teacher and their application is approved.
    Also checks if the profile exists to prevent AttributeError.
    """
    if not user.is_authenticated or user.user_type != 'teacher':
        return False

    if not hasattr(user, 'profile') or not user.profile:
        logging.warning(f"User {user.username} is a teacher but has no profile.")
        return False

    return user.profile.is_teacher_approved


# --- Core Homepage View ---
def index_view(request):
    published_courses = TeacherCourse.objects.filter(featured=True, status='published').select_related('teacher_profile__user').order_by('-created_at')
    context = {
        'page_title': 'Welcome to My Portfolio',
        'published_courses': published_courses,
        'featured_courses': published_courses,
    }
    return render(request, 'index.html', context)

# --- CV Page View ---
def cv_view(request):
    context = {}
    return render(request, 'cv.html', context)

# --- Portfolio Page View ---
def portfolio_page_view(request):
    context = {}
    return render(request, 'portfolio_page.html', context)

# --- Certificates Page View ---
def certificates_view(request):
    context = {}
    return render(request, 'certificates.html', context)

# --- Course List View ---
def course_list_view(request):
    courses = TeacherCourse.objects.filter(status='published').select_related('teacher_profile__user').order_by('-created_at')
    context = {
        'page_title': 'Our Courses & Learning',
        'courses': courses
    }
    return render(request, 'courses.html', context)

# --- Individual Course Detail View ---
def course_detail(request, course_id):
    course = get_object_or_404(TeacherCourse, id=course_id, status__in=['published', 'approved'])

    is_enrolled = False
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile:
            is_enrolled = EnrolledCourse.objects.filter(student=request.user.profile, course=course).exists()
        else:
            logging.warning(f"User {request.user.username} is authenticated but has no profile.")

    context = {
        'page_title': course.title,
        'course': course,
        'is_enrolled': is_enrolled,
    }
    return render(request, 'course_detail.html', context)

# --- Contact Page View ---
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()

            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')

        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()

    context = {
        'form': form,
        'page_title': 'Contact Us'
    }
    return render(request, 'contact.html', context)

# --- About Page View ---
def about_view(request):
    context = {}
    return render(request, 'about.html', context)

# --- Signup View ---
def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Account created successfully for {user.username}! Please log in to continue.')

            if hasattr(user, 'user_type') and user.user_type == 'teacher':
                messages.info(request, "Your teacher application is pending approval. You will be redirected to the login page.")
            else:
                messages.info(request, "Please log in with your new account.")

            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SignupForm()

    context = {
        'form': form,
    }
    return render(request, 'signup.html', context)

# --- Login View ---
def login_view(request):
    if request.method == 'GET':
        storage = messages.get_messages(request)
        storage.used = True
        if '_messages' in request.session:
            del request.session['_messages']

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                profile, created = Profile.objects.get_or_create(user=user)
                if created:
                    logging.info(f"Profile created for new user {user.username} during login.")

                if user.user_type == 'teacher':
                    if not profile.is_teacher_approved:
                        messages.error(request, "Your teacher application is pending approval. Please wait for an administrator to review it.")
                        return render(request, 'login.html', {'form': form, 'page_title': 'Login'})

                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')

                next_url = request.GET.get('next')

                if user.user_type == 'teacher' and profile.is_teacher_approved:
                    return redirect('teacher_dashboard')
                elif next_url:
                    return redirect(next_url)
                else:
                    return redirect('index')

            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please enter a valid username and password.')

    else:
        form = AuthenticationForm()

    context = {
        'form': form,
        'page_title': 'Login'
    }
    return render(request, 'login.html', context)

# --- Logout View ---
@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('index')

# --- Dashboard View (General, likely for students or general users) ---
@login_required
def dashboard(request):
    context = {
        'user': request.user,
        'page_title': 'Dashboard'
    }
    return render(request, 'dashboard.html', context)

# --- Profile View (for display) ---
@login_required
def profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    context = {
        'profile': profile,
        'user': user,
        'page_title': 'My Profile'
    }
    return render(request, 'profile.html', context)

# --- Profile Edit View ---
@login_required
def profile_edit(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('profile_edit')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = CustomUserChangeForm(instance=user)
        profile_form = ProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'page_title': 'Edit Profile'
    }
    return render(request, 'profile.html', context)

# --- Teacher Registration Stage 1 (Basic Info) ---
def teacher_register_wizard(request):
    is_authenticated = request.user.is_authenticated

    if request.method == 'POST':
        if is_authenticated:
            form = TeacherPersonalInfoForm(request.POST,
                                           user=request.user,
                                           profile_instance=request.user.profile)
        else:
            form = TeacherPersonalInfoForm(request.POST)

        if form.is_valid():
            full_name_en = form.cleaned_data['full_name_en']
            full_name_ar = form.cleaned_data['full_name_ar']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']

            request.session['teacher_data'] = {
                'full_name_en': full_name_en,
                'full_name_ar': full_name_ar,
                'email': email,
                'phone_number': phone_number,
                'is_authenticated_at_stage1': is_authenticated
            }
            request.session.modified = True

            messages.success(request, 'Basic information saved! Proceed to the next step.')
            return redirect('teacher_register_stage2')

        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        if is_authenticated:
            form = TeacherPersonalInfoForm(user=request.user, profile_instance=request.user.profile)
        else:
            form = TeacherPersonalInfoForm()

    return render(request, 'accounts/teacher_register_stage1.html', {'form': form, 'page_title': 'Teacher Application - Step 1'})

# --- Teacher Registration Stage 2 (Professional Details) ---
def teacher_register_stage2(request):
    teacher_data = request.session.get('teacher_data')
    if not teacher_data:
        messages.error(request, 'Please complete the first stage of registration.')
        return redirect('teacher_register_stage1')

    is_authenticated = request.user.is_authenticated

    if request.method == 'POST':
        if is_authenticated:
            form = TeacherProfessionalDetailsForm(request.POST, profile_instance=request.user.profile)
        else:
            form = TeacherProfessionalDetailsForm(request.POST)

        if form.is_valid():
            experience_years = form.cleaned_data['experience_years']
            university = form.cleaned_data['university']
            graduation_year = form.cleaned_data['graduation_year']
            major = form.cleaned_data['major']
            bio = form.cleaned_data['bio']

            teacher_data.update({
                'experience_years': experience_years,
                'university': university,
                'graduation_year': graduation_year,
                'major': major,
                'bio': bio,
            })
            request.session['teacher_data'] = teacher_data
            request.session.modified = True

            messages.success(request, 'Professional details saved! Proceed to review.')
            return redirect('teacher_register_confirm')

        else:
            messages.error(request, 'Please correct the errors in your professional details.')
    else:
        if is_authenticated:
            form = TeacherProfessionalDetailsForm(profile_instance=request.user.profile)
        else:
            form = TeacherProfessionalDetailsForm()

    context = {
        'form': form,
        'page_title': 'Teacher Application - Step 2',
    }
    return render(request, 'accounts/teacher_register_stage2.html', context)

# --- Teacher Registration Stage 3 (Review and Submit) ---
def teacher_register_confirm(request):
    teacher_data = request.session.get('teacher_data')

    if not teacher_data:
        messages.error(request, 'Please complete all previous stages of registration.')
        return redirect('teacher_register_stage1')

    if request.method == 'POST':
        messages.info(request, 'Review confirmed. Now set your password.')
        return redirect('teacher_register_password_setting')

    else:
        displayed_teacher_data = teacher_data.copy()

        context = {
            'teacher_data': displayed_teacher_data,
            'page_title': 'Review Your Application'
        }
        return render(request, 'accounts/teacher_register_confirm.html', context)

# --- Application Success Page View ---
def application_success_view(request):
    return render(request, 'accounts/application_success.html', {'page_title': 'Application Submitted'})

# --- Add Course View (for Approved Teachers) ---
@login_required
@user_passes_test(is_approved_teacher, login_url='login')
def add_teacher_course(request):
    teacher_profile = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':
        form = TeacherCourseForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                course = form.save(commit=False)
                course.teacher_profile = teacher_profile
                course.status = 'pending'
                course.save()
                form.save_m2m()

                messages.success(request, 'Your course has been submitted for review successfully!')
                return redirect('teacher_dashboard')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred while saving the course: {e}')
                logging.error(f"Error saving new course: {e}", exc_info=True)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherCourseForm()

    context = {
        'form': form,
        'page_title': 'Add New Course',
    }
    return render(request, 'accounts/add_teacher_course.html', context)

# --- Teacher Password Setting View ---
def teacher_register_password_setting(request):
    teacher_data = request.session.get('teacher_data')

    if not teacher_data:
        messages.error(request, 'Please complete all previous stages of registration.')
        return redirect('teacher_register_stage1')

    is_authenticated = teacher_data.get('is_authenticated_at_stage1')
    if is_authenticated and request.user.is_authenticated:
        user = request.user
        profile, created_profile = Profile.objects.get_or_create(user=user)

        profile.full_name_en = teacher_data.get('full_name_en', profile.full_name_en)
        profile.full_name_ar = teacher_data.get('full_name_ar', profile.full_name_ar)
        profile.phone_number = teacher_data.get('phone_number', profile.phone_number)
        profile.experience_years = teacher_data.get('experience_years', profile.experience_years)
        profile.university = teacher_data.get('university', profile.university)
        profile.graduation_year = teacher_data.get('graduation_year', profile.graduation_year)
        profile.major = teacher_data.get('major', profile.major)
        profile.bio = teacher_data.get('bio', profile.bio)

        if user.user_type != 'teacher':
            user.user_type = 'teacher'
            user.save()

        profile.is_teacher_application_pending = True
        profile.is_teacher_approved = False
        profile.approved_by = None
        profile.approval_date = None
        profile.rejected_by = None
        profile.rejection_date = None
        profile.rejection_reason = None

        try:
            profile.save()
            if 'teacher_data' in request.session:
                del request.session['teacher_data']
                request.session.modified = True
            messages.success(request, 'Your teacher application has been submitted successfully and is awaiting approval!')
            return redirect('application_success')
        except Exception as e:
            messages.error(f"An error occurred while saving your teacher profile: {e}")
            logging.error(f"Error updating existing user's profile for teacher application: {e}", exc_info=True)
            return redirect('teacher_register_stage1')

    if request.method == 'POST':
        form = PasswordSettingForm(request.POST)

        if form.is_valid():
            password = form.cleaned_data['password']

            full_name_en = teacher_data.get('full_name_en')
            full_name_ar = teacher_data.get('full_name_ar')
            email = teacher_data.get('email')
            phone_number = teacher_data.get('phone_number')
            experience_years = teacher_data.get('experience_years')
            university = teacher_data.get('university')
            graduation_year = teacher_data.get('graduation_year')
            major = teacher_data.get('major')
            bio = teacher_data.get('bio')

            user = None

            try:
                try:
                    user = CustomUser.objects.get(email=email)
                    messages.warning(request, "An account with this email already exists. Please log in to update your profile.")
                    return redirect('login')
                except CustomUser.DoesNotExist:
                    username_base = email.split('@')[0]
                    username = username_base
                    i = 1
                    while CustomUser.objects.filter(username=username).exists():
                        username = f"{username_base}{i}"
                        i += 1

                    user = CustomUser.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        user_type='teacher',
                        is_active=True,
                    )
                    messages.success(request, f"New account created for '{user.username}'.")

                profile, created_profile = Profile.objects.get_or_create(user=user)

                profile.full_name_en = full_name_en
                profile.full_name_ar = full_name_ar
                profile.phone_number = phone_number
                profile.experience_years = experience_years
                profile.university = university
                profile.graduation_year = graduation_year
                profile.major = major
                profile.bio = bio

                profile.is_teacher_application_pending = True
                profile.is_teacher_approved = False
                profile.approved_by = None
                profile.approval_date = None
                profile.rejected_by = None
                profile.rejection_date = None
                profile.rejection_reason = None

                profile.save()

                if 'teacher_data' in request.session:
                    del request.session['teacher_data']
                    request.session.modified = True

                messages.success(request, 'Your teacher application has been submitted successfully and is awaiting approval! You can now log in.')
                return redirect('application_success')

            except Exception as e:
                messages.error(f"An error occurred during account creation/submission: {e}")
                logging.error(f"Error during new teacher account creation/submission: {e}", exc_info=True)
                return redirect('teacher_register_stage1')

        else:
            messages.error(request, 'Please correct the password errors below.')

    else:
        form = PasswordSettingForm()

    context = {
        'form': form,
        'page_title': 'Set Your Password'
    }
    return render(request, 'accounts/teacher_register_password_setting.html', context)

# --- Teacher Dashboard View ---
@login_required
@user_passes_test(is_approved_teacher, login_url='login')
def teacher_dashboard(request):
    teacher_profile = get_object_or_404(Profile, user=request.user)
    teacher_courses = TeacherCourse.objects.filter(teacher_profile=teacher_profile).order_by('-created_at')

    context = {
        'teacher_profile': teacher_profile,
        'teacher_courses': teacher_courses,
        'page_title': 'Teacher Dashboard',
    }
    return render(request, 'accounts/teacher_dashboard.html', context)

# --- Register for Course View ---
@login_required
def register_for_course(request, course_id):
    course = get_object_or_404(TeacherCourse, id=course_id, status='published')

    if not hasattr(request.user, 'profile') or not request.user.profile:
        messages.error(request, "Your user profile is incomplete. Please update your profile before registering.")
        return redirect('course_detail', course_id=course.id)

    if EnrolledCourse.objects.filter(student=request.user.profile, course=course).exists():
        messages.info(request, f"You are already enrolled in {course.title}.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            card_number = form.cleaned_data['card_number']
            expiry_month = form.cleaned_data['expiry_month']
            expiry_year = form.cleaned_data['expiry_year']

            is_card_allowed = AllowedCard.objects.filter(
                card_number=card_number,
                expiry_month=expiry_month,
                expiry_year=expiry_year
            ).exists()

            if is_card_allowed:
                try:
                    EnrolledCourse.objects.create(
                        student=request.user.profile,
                        course=course,
                        fee_paid=course.price
                    )
                    messages.success(request, f"Payment successful! You are now enrolled in {course.title}.")
                    return redirect('course_detail', course_id=course.id)
                except IntegrityError:
                    messages.info(request, f"You are already enrolled in {course.title}.")
                    return redirect('course_detail', course_id=course.id)
                except Exception as e:
                    messages.error(f"Error completing enrollment after payment: {e}")
                    logging.error(f"Error enrolling user {request.user.username} in course {course.id}: {e}", exc_info=True)
                    return redirect('register_for_course', course_id=course.id)
            else:
                messages.error(request, "Payment failed: Card details do not match any allowed method.")
        else:
            messages.error(request, "Please correct the errors in the payment form.")
    else:
        form = PaymentForm()

    return render(request, 'payment_form.html', {'course': course, 'form': form})

# --- Student Dashboard View ---
@login_required
def student_dashboard_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    enrolled_courses_objects = EnrolledCourse.objects.filter(student=profile).select_related('course__teacher_profile__user').order_by('-enrolled_at')
    enrolled_courses = [enrolled_course.course for enrolled_course in enrolled_courses_objects]

    context = {
        'page_title': 'My Learning Dashboard',
        'student': user,
        'student_profile': profile,
        'enrolled_courses': enrolled_courses,
    }
    return render(request, 'student_dashboard.html', context)

@login_required
@require_POST
def unenroll_from_course_view(request, course_id):
    user = request.user
    profile = get_object_or_404(Profile, user=user)
    course = get_object_or_404(TeacherCourse, id=course_id)

    try:
        enrolled_course = EnrolledCourse.objects.get(student=profile, course=course)
        enrolled_course.delete()
        messages.success(request, f"You have successfully unenrolled from '{course.title}'.")
        messages.info(request, "Please note: Refunds are processed manually. Our team will contact you within 3-5 business days regarding your refund.")

    except EnrolledCourse.DoesNotExist:
        messages.error(request, "You are not enrolled in this course.")
    except Exception as e:
        messages.error(f"An error occurred while unenrolling: {e}")

    return redirect('student_dashboard')


# --- UPDATED: Teacher Reporting Views ---

@login_required
@user_passes_test(is_approved_teacher, login_url='login')
def teacher_course_reports(request):
    """
    Displays a summary report for all courses taught by the logged-in teacher,
    including total students, total fees collected, commission, and profit per course.
    Only shows courses with at least one enrolled student.
    """
    teacher_profile = request.user.profile

    # Safely convert commission_percentage to Decimal
    commission_rate_decimal = Decimal(str(teacher_profile.commission_percentage)) if teacher_profile.commission_percentage is not None else Decimal('0.00')
    commission_rate_decimal = commission_rate_decimal / Decimal('100') # Divide by 100 here to get the rate (e.g., 5.00 -> 0.05)

    # Filter courses to include only those with at least one enrollment
    # Use annotation to count students directly on the queryset
    teacher_courses_with_enrollments = TeacherCourse.objects.filter(teacher_profile=teacher_profile) \
                                                    .annotate(num_students=Count('enrolled_students')) \
                                                    .filter(num_students__gt=0) \
                                                    .order_by('title')

    report_data = []
    for course in teacher_courses_with_enrollments: # Iterate over filtered courses
        # Since we've already counted num_students, we can use it directly if available,
        # but for total_fees we still need Sum.
        enrollments = EnrolledCourse.objects.filter(course=course).select_related('student__user')

        total_fees_result = enrollments.aggregate(total_fees=Sum('fee_paid'))
        total_fees_for_course = total_fees_result['total_fees'] if total_fees_result['total_fees'] is not None else Decimal('0.00')

        commission_value = total_fees_for_course * commission_rate_decimal
        profit = total_fees_for_course - commission_value

        report_data.append({
            'course_id': course.id,
            'course_title': course.title,
            'total_students': course.num_students, # Use the annotated count
            'total_fees_collected': total_fees_for_course,
            'commission_rate': teacher_profile.commission_percentage,
            'commission_value': commission_value,
            'profit': profit,
        })

    context = {
        'report_data': report_data,
        'teacher_profile': teacher_profile,
        'page_title': 'Teacher Course Reports',
    }
    return render(request, 'accounts/teacher_reports_summary.html', context)

@login_required
@user_passes_test(is_approved_teacher, login_url='login')
def teacher_single_course_report(request, course_id):
    """
    Displays a detailed report for a single course, listing all enrolled students
    and their individual fees.
    """
    teacher_profile = request.user.profile

    course = get_object_or_404(TeacherCourse, id=course_id, teacher_profile=teacher_profile)

    enrollments = EnrolledCourse.objects.filter(course=course).select_related('student__user').order_by('student__user__username')

    students_in_course = []
    total_fees_for_course = Decimal('0.00') # Initialize as Decimal

    for enrollment in enrollments:
        students_in_course.append({
            'username': enrollment.student.user.username,
            'full_name': enrollment.student.full_name_en or enrollment.student.full_name_ar,
            'fee_paid': enrollment.fee_paid,
            'enrolled_at': enrollment.enrolled_at,
        })
        total_fees_for_course += enrollment.fee_paid

    # Safely convert commission_percentage to Decimal
    commission_rate = teacher_profile.commission_percentage if teacher_profile.commission_percentage is not None else Decimal('0.00')
    commission_rate_decimal = Decimal(str(commission_rate)) / Decimal('100') # Convert to Decimal rate

    commission_value = total_fees_for_course * commission_rate_decimal
    profit = total_fees_for_course - commission_value


    context = {
        'course': course,
        'students_in_course': students_in_course,
        'total_students': enrollments.count(),
        'total_fees_collected': total_fees_for_course,
        'commission_rate': commission_rate,
        'commission_value': commission_value,
        'profit': profit,
        'page_title': f"Report for {course.title}",
    }
    return render(request, 'accounts/teacher_single_course_report.html', context)

# --- NEW: Edit Course View (for Approved Teachers) ---
@login_required
@user_passes_test(is_approved_teacher, login_url='login')
def edit_teacher_course(request, course_id):
    teacher_profile = get_object_or_404(Profile, user=request.user)
    
    # Get the course instance, ensuring it belongs to the logged-in teacher
    course = get_object_or_404(TeacherCourse, id=course_id, teacher_profile=teacher_profile)

    if request.method == 'POST':
        form = TeacherCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            try:
                # Set status to 'pending' if it was 'published' after an edit
                # This ensures re-approval if changes are made to a published course
                if course.status == 'published' and form.has_changed():
                    course.status = 'pending'
                    messages.info(request, "Course updated and set to 'Pending Review' due to changes in a published course.")
                
                form.save()
                messages.success(request, f'Course "{course.title}" updated successfully!')
                return redirect('teacher_dashboard')
            except Exception as e:
                messages.error(request, f'An unexpected error occurred while updating the course: {e}')
                logging.error(f"Error updating course {course.id}: {e}", exc_info=True)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherCourseForm(instance=course) # Pre-populate form with existing course data

    context = {
        'form': form,
        'course': course, # Pass the course object for context if needed in the template
        'page_title': f'Edit Course: {course.title}',
    }
    # You can reuse add_teacher_course.html or create a new template if needed.
    # For now, let's assume you'll use add_teacher_course.html with slight modifications if necessary.
    return render(request, 'accounts/add_teacher_course.html', context) # Reusing the add template for simplicity



class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    form_class = ProfileForm
    model = CustomUser # Or your specific user model
    form_class = ProfileForm 
    template_name = 'accounts/profile_update.html'
    success_url = '/some-success-url/' # Or reverse_lazy('some:url_name')

    # You might have a get_object method if you're updating the current user's profile
    def get_object(self, queryset=None):
        return self.request.user
    
def health_check(request):
    """
    A simple health check view that returns HTTP 200 OK.
    """
    return HttpResponse(status=200)