# auth_system/accounts/admin.py

from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

# Import all your models
from .models import CustomUser, Profile, TeacherCourse, CourseCategory, CourseLevel, EnrolledCourse, AllowedCard


# 1. Create an Inline Admin for the Profile model
# This allows Profile fields to be edited directly when editing a CustomUser
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
                'approved_by',
                'approval_date',
                'rejected_by',
                'rejection_date',
                'rejection_reason',
            ),
            'classes': ('wide',),
        }),
    )
    # Fields can also be listed directly if not using fieldsets, eg:
    # fields = ('full_name_en', 'full_name_ar', 'phone_number', 'bio', 'profile_picture', ...)


# --- Custom Admin for CustomUser ---
@admin.register(CustomUser) # Using decorator for CustomUser as well for consistency
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
    inlines = [ProfileInline] # Link ProfileInline here to show Profile fields when editing a User


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
        'user__user_type', # Filter profiles by the user's type
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
    raw_id_fields = ('user', 'approved_by', 'rejected_by') # Useful for ForeignKey fields

    # Add custom admin actions here
    actions = ['approve_teacher_applications', 'reject_teacher_applications']

    # --- Admin Action: Approve Teacher Applications ---
    def approve_teacher_applications(self, request, queryset):
        updated_count = 0
        for profile in queryset:
            # Only process if it's a teacher and the application is pending
            # (or if it was approved and needs re-approval, etc. - adjust logic as needed)
            if profile.user.user_type == 'teacher' and profile.is_teacher_application_pending:
                profile.is_teacher_application_pending = False
                profile.is_teacher_approved = True
                profile.approved_by = request.user
                profile.approval_date = timezone.now()
                profile.rejected_by = None # Clear rejection details
                profile.rejection_date = None
                profile.rejection_reason = None
                profile.save()
                updated_count += 1
        self.message_user(
            request,
            f"{updated_count} teacher application(s) successfully approved.",
            messages.SUCCESS
        )
    approve_teacher_applications.short_description = "Approve selected teacher applications"

    # --- Admin Action: Reject Teacher Applications ---
    def reject_teacher_applications(self, request, queryset):
        updated_count = 0
        for profile in queryset:
            # Only process if it's a teacher and the application is pending
            if profile.user.user_type == 'teacher' and profile.is_teacher_application_pending:
                profile.is_teacher_application_pending = False
                profile.is_teacher_approved = False
                profile.rejected_by = request.user
                profile.rejection_date = timezone.now()
                profile.approved_by = None # Clear approval details
                profile.approval_date = None
                profile.save()
                updated_count += 1
        self.message_user(
            request,
            f"{updated_count} teacher application(s) successfully rejected.",
            messages.WARNING
        )
    reject_teacher_applications.short_description = "Reject selected teacher applications"

    # Custom method to display the username as a clickable link
    def username_link(self, obj):
        link = reverse("admin:%s_%s_change" % (obj.user._meta.app_label, obj.user._meta.model_name), args=[obj.user.id])
        return format_html('<a href="%s">%s</a>' % (link, obj.user.username))
    username_link.short_description = 'User'
    username_link.admin_order_field = 'user__username'

    # Custom method to display the user type
    def user_type(self, obj):
        return obj.user.user_type
    user_type.short_description = 'User Type'
    user_type.admin_order_field = 'user__user_type'


# --- Custom Admin for CourseCategory ---
@admin.register(CourseCategory) # Using decorator for consistency
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# --- Custom Admin for CourseLevel ---
@admin.register(CourseLevel) # Using decorator for consistency
class CourseLevelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


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
        'status',
        'created_at',
        'updated_at',
        'is_published_display', # This will show a checkmark if status is 'published'
    )
    list_filter = (
        'status',
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
    ordering = ('-created_at',) # Default ordering

    fieldsets = (
        (None, {
            'fields': ('teacher_profile', 'title', 'description', 'price', 'language')
        }),
        ('Categorization', {
            'fields': ('categories', 'level'),
        }),
        ('Media', {
            'fields': ('course_picture', 'video_trailer_url'),
            'classes': ('collapse',)
        }),
        ('Course Status', { # Admin will primarily change status here
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at') # These fields are automatically set

    # Custom method to display 'Published' status clearly in list_display
    def is_published_display(self, obj):
        return obj.status == 'published'
    is_published_display.boolean = True # Display as a nice checkmark/X
    is_published_display.short_description = 'Published'

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

    # --- Custom Admin Actions for Course Approval/Publishing ---
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
        # Only allow transition to 'published' from 'approved' or 'pending' for logical flow
        updated_count = queryset.filter(status__in=['approved', 'pending']).update(status='published')
        if updated_count > 0:
            self.message_user(request, f"{updated_count} course(s) successfully marked as 'Published'.")
        else:
            self.message_user(request, "No eligible courses selected for publishing (must be Approved or Pending).", level='warning')
    mark_as_published.short_description = "Mark selected as Published (Available to Customers)"
    
@admin.register(AllowedCard)
class AllowedCardAdmin(admin.ModelAdmin):
    list_display = ('card_number', 'expiry_month', 'expiry_year', 'added_at')
    search_fields = ('card_number',)
    list_filter = ('expiry_year',)
    # You might want to make card_number read-only after creation for security,
    # or limit who can add/change these.
    # fields = ('card_number', 'expiry_month', 'expiry_year') # Or use fieldsets/inlines