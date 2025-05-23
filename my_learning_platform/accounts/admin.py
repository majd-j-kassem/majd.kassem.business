# accounts/admin.py

from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils import timezone
# Removed TemplateResponse, JsonResponse, and json as they are not needed for direct form submission
# from django.template.response import TemplateResponse
# from django.http import HttpResponseRedirect, JsonResponse
# import json
from django.shortcuts import get_object_or_404

from .models import ContactMessage
from .models import CustomUser, Profile, TeacherCourse, CourseCategory, CourseLevel, EnrolledCourse, AllowedCard
from .forms import TeacherCourseForm # Assuming this form still exists and is needed elsewhere

# 1. Create an Inline Admin for the Profile model (No change needed here)
class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = 'user'
    can_delete = False
    verbose_name_plural = 'Profile Info'

    fieldsets = (
        ('Basic Information', {
            'fields': ('full_name_en', 'full_name_ar', 'phone_number', 'bio', 'profile_picture')
        }),
        ('Teacher Professional Details', {
            'fields': ('experience_years', 'university', 'graduation_year', 'major'),
            'classes': ('collapse',),
        }),
        ('Teacher Application Status',
         {
            'fields': (
                'is_teacher_application_pending',
                'is_teacher_approved',
                'commission_percentage',
                'approved_by',
                'approval_date',
                'rejected_by',
                'rejection_date',
                'rejection_reason',
            ),
            'classes': ('wide',),
        }),
    )
    # These fields are generally read-only on the inline form to avoid accidental changes
    # from the CustomUser admin page. The main ProfileAdmin will handle detailed editing.
    readonly_fields = (
        'is_teacher_approved', 'commission_percentage', 'approved_by', 'approval_date',
        'rejected_by', 'rejection_date', 'rejection_reason'
    )

# --- Custom Admin for CustomUser (No change needed here) ---
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'user_type',
        'is_staff',
        'is_active',
        'get_full_name_en',
        'get_full_name_ar',
        'date_joined',
        'is_teacher_approved_display',
    )
    list_filter = ('user_type', 'is_staff', 'is_active', 'profile__is_teacher_approved')
    search_fields = (
        'username',
        'email',
        'profile__full_name_en',
        'profile__full_name_ar'
    )
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    inlines = [ProfileInline]

    def get_full_name_en(self, obj):
        return obj.profile.full_name_en if hasattr(obj, 'profile') else ''
    get_full_name_en.short_description = 'Full Name (English)'

    def get_full_name_ar(self, obj):
        return obj.profile.full_name_ar if hasattr(obj, 'profile') else ''
    get_full_name_ar.short_description = 'Full Name (Arabic)'

    @admin.display(boolean=True, description='Teacher Approved')
    def is_teacher_approved_display(self, obj):
        return obj.profile.is_teacher_approved if hasattr(obj, 'profile') else False


# --- Custom Admin for Profile: The Core Changes ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # CRITICAL: This tells Django to use our custom template for the profile change page.
    # You MUST create this file at 'your_project_root/templates/admin/accounts/profile/change_form.html'
    change_form_template = 'accounts/change_form.html'

    list_display = (
        'username_link',
        'user_type_display',
        'is_teacher_application_pending',
        'is_teacher_approved',
        'commission_percentage',
        'approved_by_username',
        'approval_date',
        'rejection_reason',
        'full_name_en',
        'full_name_ar',
        'phone_number',
        # REMOVED: 'approval_actions_button' from list_display as actions are now on the detail page
        # and no longer rely on separate pop-up views from the list.
    )
    list_filter = (
        'is_teacher_application_pending',
        'is_teacher_approved',
        'user__user_type',
    )
    search_fields = (
        'user__username',
        'user__email',
        'full_name_en',
        'full_name_ar',
        'phone_number',
    )
    fieldsets = (
        (None, {
            'fields': ('user', 'profile_picture', 'bio', 'phone_number')
        }),
        ('Teacher Professional Details', {
            'fields': ('experience_years', 'university', 'graduation_year', 'major', 'full_name_en', 'full_name_ar'),
            'classes': ('collapse',),
        }),
        ('Teacher Application Status', {
            'fields': (
                'is_teacher_application_pending',
                'is_teacher_approved',
                'commission_percentage', # This field is now managed by get_readonly_fields
                'approved_by',
                'approval_date',
                'rejected_by',
                'rejection_date',
                'rejection_reason'
            ),
        }),
    )
    raw_id_fields = ('user', 'approved_by', 'rejected_by')
    # --- Conditional Readonly Fields ---
    # This method dynamically determines which fields are read-only based on the object's state.
    def get_readonly_fields(self, request, obj=None):
        # Fields that are always read-only
        read_only_fields = (
            'user', # Prevent changing the user linked to the profile
            'is_teacher_approved', # Managed by our custom actions, not direct editing
            'approved_by',
            'approval_date',
            'rejected_by',
            'rejection_date',
        )

        # If we are adding a new object (obj is None), commission_percentage and rejection_reason
        # are not applicable yet, so make them read-only.
        if obj is None:
            return read_only_fields + ('commission_percentage', 'rejection_reason',)

        # If it's an existing object (editing) and it's a teacher profile
        if obj.user.user_type == 'teacher':
            if obj.is_teacher_approved:
                # If the teacher is already approved, make commission_percentage and rejection_reason read-only.
                # You can still modify commission_percentage for an approved teacher by editing it and
                # just clicking the standard 'Save' button (which doesn't trigger the 'action' logic).
                return read_only_fields + ('rejection_reason',) # Commission is editable for approved if not explicitly read-only here
            else:
                # If it's a pending teacher application, commission_percentage should be editable
                # (to set it during approval) and rejection_reason should also be editable (for rejection).
                # So, we do NOT add them to readonly_fields here.
                return read_only_fields
        else:
            # For non-teacher profiles, commission_percentage and rejection_reason are not relevant
            # and should always be read-only.
            return read_only_fields + ('commission_percentage', 'rejection_reason',)


    # KEY CHANGE: Remove batch actions to hide the dropdown and "Go" button
    actions = []

    # REMOVED: The batch approval/rejection methods are no longer relevant
    # since we're handling approval/rejection on the detail page directly.
    # def approve_teacher_applications_batch(self, request, queryset): ...
    # def reject_teacher_applications_batch(self, request, queryset): ...


    # --- Utility methods for list_display ---
    def username_link(self, obj):
        # This link now points to the Profile change page directly.
        # This is more intuitive for managing profile-specific details.
        link = reverse("admin:{}_{}_change".format(self.model._meta.app_label, self.model._meta.model_name), args=[obj.id])
        return format_html('<a href="%s">%s</a>' % (link, obj.user.username))
    username_link.short_description = 'User'
    username_link.admin_order_field = 'user__username' # Allows sorting by username

    def user_type_display(self, obj):
        return obj.user.get_user_type_display()
    user_type_display.short_description = 'User Type'
    user_type_display.admin_order_field = 'user__user_type'

    def approved_by_username(self, obj):
        return obj.approved_by.username if obj.approved_by else '-'
    approved_by_username.short_description = "Approved By"

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('user', 'approved_by', 'rejected_by')
        return qs

    # REMOVED: Custom URLs for pop-up approval and rejection are no longer needed
    # as the logic is now handled by save_model on the standard form submission.
    def get_urls(self):
        return super().get_urls()

    # REMOVED: approval_actions_button is removed from list_display and therefore this method
    # is no longer needed.
    # def approval_actions_button(self, obj): ...

    # REMOVED: process_approve_commission and process_reject_application methods are removed
    # as their functionality is now integrated into the save_model method.
    # def process_approve_commission(self, request, object_id): ...
    # def process_reject_application(self, request, object_id): ...


    # --- OVERRIDE save_model TO HANDLE APPROVAL/REJECTION LOGIC ---
    def save_model(self, request, obj, form, change):
        # CORRECTED: Check for the button names directly in request.POST
        is_approve_button_pressed = '_approve_teacher' in request.POST
        is_reject_button_pressed = '_reject_teacher' in request.POST

        # Apply this custom logic only if the profile belongs to a teacher
        if obj.user.user_type == 'teacher':
            if is_approve_button_pressed and not obj.is_teacher_approved:
                # Get the commission percentage from the submitted form data
                commission_percentage = form.cleaned_data.get('commission_percentage')

                # Server-side validation for commission_percentage
                if commission_percentage is None or not (0 <= commission_percentage <= 100):
                    messages.error(request, "Commission percentage must be between 0 and 100 to approve.")
                    return # IMPORTANT: Do NOT call super().save_model() here

                # If the application is not pending, warn the admin but allow saving other profile changes.
                if not obj.is_teacher_application_pending:
                    messages.warning(request, "This application is no longer pending, but status will be changed to approved.")

                # Update profile fields for approval
                obj.is_teacher_approved = True
                obj.is_teacher_application_pending = False
                obj.approved_by = request.user
                obj.approval_date = timezone.now()
                obj.rejected_by = None
                obj.rejection_date = None
                obj.rejection_reason = None
                obj.commission_percentage = commission_percentage # Apply the commission from the form

                messages.success(request, f"Teacher '{obj.user.username}' approved with {commission_percentage}% commission.")
                obj.save() # Explicitly save the object with changes here
                return # Crucial: Return here to prevent super().save_model from saving again

            elif is_reject_button_pressed and not obj.is_teacher_approved:
                # Get the rejection reason from the submitted form data
                rejection_reason = form.cleaned_data.get('rejection_reason')

                # Server-side validation for rejection reason
                if not rejection_reason or rejection_reason.strip() == '':
                    messages.error(request, "Rejection reason is required to reject the application.")
                    return # DO NOT call super().save_model() here

                # If the application is not pending, warn the admin but allow saving other profile changes.
                if not obj.is_teacher_application_pending:
                    messages.warning(request, "This application is no longer pending, but status will be changed to rejected.")

                # Update profile fields for rejection
                obj.is_teacher_approved = False
                obj.is_teacher_application_pending = False
                obj.rejected_by = request.user
                obj.rejection_date = timezone.now()
                obj.rejection_reason = rejection_reason
                obj.approved_by = None
                obj.approval_date = None
                obj.commission_percentage = 0.00 # Reset commission on rejection

                messages.warning(request, f"Teacher '{obj.user.username}' application rejected.")
                obj.save() # Explicitly save the object with changes here
                return # Crucial: Return here to prevent super().save_model from saving again

            # If no specific action button was pressed (e.g., just the general "Save" button was clicked),
            # or if the teacher is already approved/rejected and the admin just saved general profile info.
            # This block will now be reached if no special button was pressed, or if the status
            # doesn't allow for approval/rejection (e.g., already approved).
            messages.info(request, "Saving general profile updates for this teacher profile.")

        else:
            # For non-teacher profiles, just save normally.
            messages.info(request, "Saving general profile updates for non-teacher profile.")

        # Always call the superclass's save_model to persist the object to the database,
        # UNLESS one of the specific button actions was handled and returned early.
        super().save_model(request, obj, form, change)



    # --- Media Class: Load our custom JavaScript for direct actions ---
    

# --- Remaining Admin Classes (No changes needed) ---

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(CourseLevel)
class CourseLevelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    form = TeacherCourseForm

    list_display = (
        'title',
        'teacher_profile_link',
        'get_categories_display',
        'level',
        'price',
        'language',
        'featured',
        'status',
        'created_at',
        'updated_at',
        'is_published_display',
    )
    list_filter = (
        'status',
        'featured',
        'categories',
        'level',
        'language',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'title',
        'description',
        'teacher_profile__user__username',
        'language',
    )
    raw_id_fields = ('teacher_profile',)
    filter_horizontal = ('categories',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    fieldsets = (
        (None, {
            'fields': ('teacher_profile', 'title', 'description', 'price', 'language', 'featured')
        }),
        ('Categorization', {
            'fields': ('categories', 'level'),
        }),
        ('Media', {
            'fields': ('course_picture', 'video_trailer_url'),
            'classes': ('collapse',)
        }),
        ('Course Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def is_published_display(self, obj):
        return obj.status == 'published'
    is_published_display.boolean = True
    is_published_display.short_description = 'Published'

    def teacher_profile_link(self, obj):
        link = reverse("admin:%s_%s_change" % (obj.teacher_profile._meta.app_label, obj.teacher_profile._meta.model_name), args=[obj.teacher_profile.id])
        return format_html('<a href="%s">%s</a>' % (link, obj.teacher_profile.user.username))
    teacher_profile_link.short_description = 'Teacher'
    teacher_profile_link.admin_order_field = 'teacher_profile__user__username'

    def get_categories_display(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])
    get_categories_display.short_description = 'Categories'

    actions = ['mark_as_pending_review', 'mark_as_approved', 'mark_as_rejected', 'mark_as_published']

    def mark_as_pending_review(self, request, queryset):
        queryset.update(status='pending')
        self.message_user(request, "Selected courses marked as 'Pending Review'.")
    mark_as_pending_review.short_description = "Mark selected as Pending Review"

    def mark_as_approved(self, request, queryset):
        queryset.update(status='approved')
        self.message_user(request, "Selected courses marked as 'Approved'.")
    mark_as_approved.short_description = "Mark selected as Approved"

    def mark_as_rejected(self, request, queryset):
        queryset.update(status='rejected')
        self.message_user(request, "Selected courses marked as 'Rejected'.")
    mark_as_rejected.short_description = "Mark selected as Rejected"

    def mark_as_published(self, request, queryset):
        updated_count = queryset.filter(status__in=['approved', 'pending']).update(status='published')
        if updated_count > 0:
            self.message_user(request, f"{updated_count} course(s) successfully marked as 'Published'.")
        else:
            self.message_user(request, "No eligible courses selected for publishing (must be Approved or Pending).", level='warning')
    mark_as_published.short_description = "Mark selected as Published (Available to Customers)"

@admin.register(EnrolledCourse)
class EnrolledCourseAdmin(admin.ModelAdmin):
    list_display = ('student_username', 'course_title', 'enrolled_at')
    list_filter = ('enrolled_at', 'course__level', 'course__categories')
    search_fields = ('student__user__username', 'course__title')
    raw_id_fields = ('student', 'course')

    def student_username(self, obj):
        return obj.student.user.username
    student_username.short_description = 'Student Username'
    student_username.admin_order_field = 'student__user__username'

    def course_title(self, obj):
        return obj.course.title
    course_title.short_description = 'Course Title'
    course_title.admin_order_field = 'course__title'


@admin.register(AllowedCard)
class AllowedCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'expiry_month', 'expiry_year', 'added_at')
    search_fields = ('card_number',)
    list_filter = ('expiry_year',)

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'submitted_at')
    search_fields = ('name', 'email', 'message')
    list_filter = ('submitted_at',)
    readonly_fields = ('name', 'email', 'phone_number', 'message', 'submitted_at')
    date_hierarchy = 'submitted_at'