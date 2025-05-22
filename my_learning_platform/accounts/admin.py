# accounts/admin.py

from django.contrib import admin, messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import ContactMessage # Import your new model

# Import all your models
from .models import CustomUser, Profile, TeacherCourse, CourseCategory, CourseLevel, EnrolledCourse, AllowedCard

# Import your forms (THIS IS THE CRUCIAL PART FOR TEACHERCOURSEADMIN)
from .forms import TeacherCourseForm # <-- ADD THIS IMPORT
# If you have CustomUserCreationForm and CustomUserChangeForm, import them here as well
# from .forms import CustomUserCreationForm, CustomUserChangeForm


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


# --- Custom Admin for CustomUser ---
# NOTE: If you are extending Django's built-in UserAdmin, you would inherit from BaseUserAdmin
# If not, admin.ModelAdmin is fine, but you'll need to define fieldsets/add_fieldsets yourself.
# Assuming you're not using CustomUserCreationForm/ChangeForm with BaseUserAdmin for simplicity here.
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin): # Use BaseUserAdmin if inheriting from AbstractUser properly
    list_display = (
        'username',
        'email',
        'user_type',
        'is_staff',
        'is_active',
        'get_full_name_en',
        'get_full_name_ar',
        'date_joined',
        'is_teacher_approved_display', # Added for clarity in CustomUser list
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


# --- Custom Admin for Profile with Approve/Reject Actions ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        'username_link',
        'user_type_display', # Changed from user_type to avoid conflict if user_type exists in Profile
        'is_teacher_application_pending',
        'is_teacher_approved',
        'approved_by',
        'approval_date',
        'rejected_by',
        'rejection_date',
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
    raw_id_fields = ('user', 'approved_by', 'rejected_by')

    actions = ['approve_teacher_applications', 'reject_teacher_applications']

    def approve_teacher_applications(self, request, queryset):
        updated_count = 0
        for profile in queryset:
            if profile.user.user_type == 'teacher' and profile.is_teacher_application_pending:
                profile.is_teacher_application_pending = False
                profile.is_teacher_approved = True
                profile.approved_by = request.user
                profile.approval_date = timezone.now()
                profile.rejected_by = None
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

    def reject_teacher_applications(self, request, queryset):
        updated_count = 0
        for profile in queryset:
            if profile.user.user_type == 'teacher' and profile.is_teacher_application_pending:
                profile.is_teacher_application_pending = False
                profile.is_teacher_approved = False
                profile.rejected_by = request.user
                profile.rejection_date = timezone.now()
                profile.approved_by = None
                profile.approval_date = None
                profile.save()
                updated_count += 1
        self.message_user(
            request,
            f"{updated_count} teacher application(s) successfully rejected.",
            messages.WARNING
        )
    reject_teacher_applications.short_description = "Reject selected teacher applications"

    def username_link(self, obj):
        link = reverse("admin:%s_%s_change" % (obj.user._meta.app_label, obj.user._meta.model_name), args=[obj.user.id])
        return format_html('<a href="%s">%s</a>' % (link, obj.user.username))
    username_link.short_description = 'User'
    username_link.admin_order_field = 'user__username'

    # Corrected method name to avoid conflict with potential Profile.user_type field
    def user_type_display(self, obj):
        return obj.user.get_user_type_display() # Use get_FOO_display for choices field
    user_type_display.short_description = 'User Type'
    user_type_display.admin_order_field = 'user__user_type'


# --- Custom Admin for CourseCategory ---
@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# --- Custom Admin for CourseLevel ---
@admin.register(CourseLevel)
class CourseLevelAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# --- Custom Admin for TeacherCourse (THE MAIN FIX IS HERE) ---
@admin.register(TeacherCourse)
class TeacherCourseAdmin(admin.ModelAdmin):
    form = TeacherCourseForm # <-- THIS IS THE CRITICAL LINE TO ADD!

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
    # AllowedCard doesn't explicitly need a form=... if it's simple enough
    # and not relying on complex form customizations.
    # fields = ('card_number', 'expiry_month', 'expiry_year') # Or use fieldsets/inlines
    
@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'submitted_at')
    search_fields = ('name', 'email', 'message')
    list_filter = ('submitted_at',)
    readonly_fields = ('name', 'email', 'phone_number', 'message', 'submitted_at') # Make fields read-only in admin
    date_hierarchy = 'submitted_at' # Add a date hierarchy for navigation
