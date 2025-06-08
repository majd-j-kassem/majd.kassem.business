from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils import timezone
from django.shortcuts import get_object_or_404
from decimal import Decimal # Ensure Decimal is imported for commission percentage handling

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
            'classes': ('collapse',)
        }),
        ('Teacher Application Status', {
            'fields': (
                'is_teacher_application_pending',
                'is_teacher_approved',
                'commission_percentage',
                'approved_by',
                'approval_date',
                'rejected_by',
                'rejection_date',
                'rejection_reason'
            ),
        }),
    )
    raw_id_fields = ('user', 'approved_by', 'rejected_by')

    def get_readonly_fields(self, request, obj=None):
        read_only_fields = (
            'user',
            'is_teacher_approved',
            'approved_by',
            'approval_date',
            'rejected_by',
            'rejection_date',
        )

        if obj is None: # Adding a new object
            return read_only_fields + ('commission_percentage', 'rejection_reason', 'is_teacher_application_pending',)

        # For existing teacher profiles
        if obj.user.user_type == 'teacher':
            if obj.is_teacher_approved: # Teacher is currently approved
                return read_only_fields + ('rejection_reason', 'is_teacher_application_pending',)
            else: # Teacher is pending OR deactivated (is_teacher_approved is False)
                # commission_percentage and rejection_reason should be editable for these states
                return read_only_fields
        else: # Not a teacher profile
            return read_only_fields + ('commission_percentage', 'rejection_reason', 'is_teacher_application_pending',)


    actions = []

    # --- Utility methods for list_display (KEEP AS IS) ---
    def username_link(self, obj):
        link = reverse("admin:{}_{}_change".format(self.model._meta.app_label, self.model._meta.model_name), args=[obj.id])
        return format_html('<a href="%s">%s</a>' % (link, obj.user.username))
    username_link.short_description = 'User'
    username_link.admin_order_field = 'user__username'

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


    # --- OVERRIDE save_model TO HANDLE APPROVAL/REJECTION/DEACTIVATION LOGIC ---
    def save_model(self, request, obj, form, change):
        is_approve_button_pressed = '_approve_teacher' in request.POST
        is_reject_button_pressed = '_reject_teacher' in request.POST # Ensure this is correct

        # Removed is_activate_button_pressed as it's no longer used

        # Apply this custom logic only if the profile belongs to a teacher
        if obj.user.user_type == 'teacher':

            # --- Handle APPROVAL for PENDING or DEACTIVATED teacher ---
            # This condition now covers both initial pending and a deactivated teacher
            if is_approve_button_pressed and not obj.is_teacher_approved:
                commission_percentage = form.cleaned_data.get('commission_percentage')
                if commission_percentage is None or not (0 <= commission_percentage <= 100):
                    messages.error(request, "Commission percentage must be between 0 and 100 to approve.")
                    return # Stop processing, prevent save

                obj.is_teacher_approved = True
                obj.is_teacher_application_pending = False # No longer pending
                obj.approved_by = request.user
                obj.approval_date = timezone.now()
                obj.rejected_by = None
                obj.rejection_date = None
                obj.rejection_reason = None
                obj.commission_percentage = commission_percentage
                messages.success(request, f"Teacher '{obj.user.username}' approved with {commission_percentage}% commission.")
                obj.save()
                return

            # --- Handle REJECTION for PENDING or DEACTIVATED teacher ---
            # This condition now covers both initial pending and a deactivated teacher
            elif is_reject_button_pressed and not obj.is_teacher_approved:
                rejection_reason = form.cleaned_data.get('rejection_reason')
                if not rejection_reason or rejection_reason.strip() == '':
                    messages.error(request, "Rejection reason is required to reject the application.")
                    return # DO NOT call super().save_model() here

                obj.is_teacher_approved = False
                obj.is_teacher_application_pending = False # No longer pending
                obj.rejected_by = request.user
                obj.rejection_date = timezone.now()
                obj.rejection_reason = rejection_reason
                obj.approved_by = None
                obj.approval_date = None
                obj.commission_percentage = Decimal('0.00') # Reset commission on rejection
                messages.warning(request, f"Teacher '{obj.user.username}' application rejected.")
                obj.save()
                return

            # --- Handle DEACTIVATION of APPROVED teacher ---
            # This logic remains the same
            elif '_deactivate_teacher' in request.POST and obj.is_teacher_approved:
                rejection_reason = form.cleaned_data.get('rejection_reason')
                if not rejection_reason or rejection_reason.strip() == '':
                     rejection_reason = "Deactivated by admin."

                obj.is_teacher_approved = False
                obj.is_teacher_application_pending = False # Set to false upon deactivation
                obj.approved_by = None
                obj.approval_date = None
                obj.rejected_by = request.user
                obj.rejection_date = timezone.now()
                obj.rejection_reason = rejection_reason
                obj.commission_percentage = Decimal('0.00') # Reset commission to zero upon deactivation
                messages.warning(request, f"Teacher '{obj.user.username}' has been deactivated.")
                obj.save()
                return

            # --- Handle General Save (if no specific button was pressed) ---
            messages.info(request, "General profile updates for this teacher profile are being saved.")

        else:
            messages.info(request, "Saving general profile updates for non-teacher profile.")

        super().save_model(request, obj, form, change)


# --- Remaining Admin Classes (KEEP AS IS) ---
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
        'is_published_display',
        'get_categories_display',
        'level',
        'price',
        'language',
        'featured',
        'status',
        'created_at',
        'updated_at',
        
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