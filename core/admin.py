
from django.contrib import admin
from .models import (
    StudentProfile,
    Country,
    University,
    Course,
    CourseShortlist,
    Appointment,
    CounselorAvailability,
    StudentDocument,
    StudentApplication, 
    ApplicationStatusHistory,
    CounselorNote,
)
from core.models import Notification



@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "highest_qualification",
        "preferred_study_level",
        "preferred_country",
    )
    search_fields = ("user__username", "user__email")
    list_filter = ("preferred_study_level", "preferred_country")


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "currency", "official_language", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "city", "is_active")
    search_fields = ("name", "city")
    list_filter = ("country", "is_active")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "university",
        "study_level",
        "annual_tuition_fee",
        "currency",
        "is_active",
    )
    search_fields = ("name", "university__name")
    list_filter = ("study_level", "currency", "is_active")


@admin.register(CourseShortlist)
class CourseShortlistAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "created_at")
    search_fields = (
        "student__username",
        "student__email",
        "course__name",
        "course__university__name",
    )
    list_filter = ("created_at",)
    readonly_fields = ("created_at",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "counselor",
        "appointment_datetime",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "appointment_datetime",
    )

    search_fields = (
        "student__username",
        "student__email",
        "counselor__username",
        "counselor__email",
    )

    ordering = ("appointment_datetime",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(CounselorAvailability)
class CounselorAvailabilityAdmin(admin.ModelAdmin):
    list_display = (
        "counselor",
        "start_datetime",
        "end_datetime",
        "is_available",
    )

    list_filter = (
        "is_available",
        "start_datetime",
    )

    search_fields = (
        "counselor__username",
        "counselor__email",
    )

    ordering = ("start_datetime",)

@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "student",
        "document_type",
        "status",
        "uploaded_at",
    )
    list_filter = ("document_type", "status", "uploaded_at")
    search_fields = (
        "title",
        "student__username",
        "student__email",
    )
    readonly_fields = (
        "uploaded_at",
        "updated_at",
        "reviewed_at",
    )

    
@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "reference_code",
        "student",
        "course",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "reference_code",
        "student__username",
        "student__email",
        "course__name",
    )
    readonly_fields = (
        "reference_code",
        "created_at",
        "updated_at",
    )


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "application",
        "previous_status",
        "new_status",
        "changed_by",
        "changed_at",
    )
    list_filter = ("new_status", "changed_at")
    search_fields = (
        "application__reference_code",
        "application__student__username",
        "note",
    )
    readonly_fields = ("changed_at",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "recipient",
        "application",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "created_at")
    search_fields = (
        "title",
        "message",
        "recipient__username",
        "recipient__email",
    )
    readonly_fields = ("created_at",)


@admin.register(CounselorNote)
class CounselorNoteAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "counselor",
        "student",
        "application",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "title",
        "note",
        "counselor__username",
        "student__username",
    )
    readonly_fields = ("created_at", "updated_at")
