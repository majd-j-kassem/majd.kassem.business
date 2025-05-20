# auth_system/accounts/admin.py

from django.contrib import admin, messages # Import messages for user feedback
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone # Import timezone to get current date/time

# Import all your models
from .models import CustomUser, Profile, CourseCategory, CourseLevel, TeacherCourse


# --- Custom Admin for CustomUser ---
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'user_type')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)


# --- Custom Admin for Profile with Approve/Reject Actions ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'username_link',
        'user_type',
        'is_teacher_application_pending',
        'is_teacher_approved',
        'approved_by',
        'approval_date',
        'rejected_by',
        'rejection_date',
        'full_name_en',
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
            'classes': ('collapse',),
        }),
        ('Teacher Application Status', {
            'fields': (
                'is_teacher_application_pending',
                'is_teacher_approved',
                'approved_by',
                'approval_date',
                'rejected_by',
                'rejection_date',
                'rejection_reason'
            ),
        }),
    )

    # Add custom admin actions here
    actions = ['approve_teacher_applications', 'reject_teacher_applications']

    # --- Admin Action: Approve Teacher Applications ---
    def approve_teacher_applications(self, request, queryset):
        updated_count = 0
        for profile in queryset:
            # Only process if it's a teacher and the application is pending
            if profile.user.user_type == 'teacher' and profile.is_teacher_application_pending:
                profile.is_teacher_application_pending = False
                profile.is_teacher_approved = True
                profile.approved_by = request.user # Set the admin who approved
                profile.approval_date = timezone.now() # Record approval time
                # Clear any previous rejection details
                profile.rejected_by = None
                profile.rejection_date = None
                profile.rejection_reason = None
                profile.save()
                updated_count += 1
        self.message_user(
            request,
            f"{updated_count} teacher application(s) successfully approved.",
            messages.SUCCESS # Display a success message
        )
    # Short description for the action in the admin dropdown
    approve_teacher_applications.short_description = "Approve selected teacher applications"

    # --- Admin Action: Reject Teacher Applications ---
    def reject_teacher_applications(self, request, queryset):
        updated_count = 0
        for profile in queryset:
            # Only process if it's a teacher and the application is pending
            if profile.user.user_type == 'teacher' and profile.is_teacher_application_pending:
                profile.is_teacher_application_pending = False
                profile.is_teacher_approved = False # Explicitly set to False for rejection
                profile.rejected_by = request.user # Set the admin who rejected
                profile.rejection_date = timezone.now() # Record rejection time
                # Clear any previous approval details
                profile.approved_by = None
                profile.approval_date = None
                # Note: For batch rejection, we don't prompt for a reason here.
                # The admin can edit individual profiles to add a rejection_reason if needed.
                profile.save()
                updated_count += 1
        self.message_user(
            request,
            f"{updated_count} teacher application(s) successfully rejected.",
            messages.WARNING # Display a warning message for rejection
        )
    # Short description for the action in the admin dropdown
    reject_teacher_applications.short_description = "Reject selected teacher applications"


    # Custom method to display the username as a clickable link to the CustomUser's admin page
    def username_link(self, obj):
        link = reverse("admin:%s_%s_change" % (obj.user._meta.app_label, obj.user._meta.model_name), args=[obj.user.id])
        return format_html('<a href="%s">%s</a>' % (link, obj.user.username))
    username_link.short_description = 'User'
    username_link.admin_order_field = 'user__username'

    # Custom method to display the user type from the related CustomUser
    def user_type(self, obj):
        return obj.user.user_type
    user_type.short_description = 'User Type'
    user_type.admin_order_field = 'user__user_type'


# Register basic models (CourseCategory and CourseLevel don't need custom admin classes yet)
admin.site.register(CourseCategory)
admin.site.register(CourseLevel)


# --- Custom Admin for TeacherCourse ---
@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'teacher_profile_link',
        'get_categories_display',
        'level',
        'price',
        'language',
    )
    list_filter = (
        'categories',
        'level',
        'language',
    )
    search_fields = (
        'title',
        'description',
        'teacher_profile__user__username',
        'language',
    )
    fieldsets = (
        (None, {
            'fields': ('teacher_profile', 'title', 'description', 'price', 'language')
        }),
        ('Course Details', {
            'fields': ('categories', 'level'),
        }),
    )

    # Custom method to display the teacher's username as a link to their profile
    def teacher_profile_link(self, obj):
        link = reverse("admin:%s_%s_change" % (obj.teacher_profile._meta.app_label, obj.teacher_profile._meta.model_name), args=[obj.teacher_profile.id])
        return format_html('<a href="%s">%s</a>' % (link, obj.teacher_profile.user.username))
    teacher_profile_link.short_description = 'Teacher'
    teacher_profile_link.admin_order_field = 'teacher_profile__user__username'

    # Custom method to display ManyToMany categories nicely
    def get_categories_display(self, obj):
        return ", ".join([category.name for category in obj.categories.all()])
    get_categories_display.short_description = 'Categories'