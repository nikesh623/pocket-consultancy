
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "dashboard/student/",
        views.student_dashboard,
        name="student_dashboard",
    ),
    path(
        "dashboard/counselor/",
        views.counselor_dashboard,
        name="counselor_dashboard",
    ),
    path(
        "dashboard/documentation/",
        views.documentation_dashboard,
        name="documentation_dashboard",
    ),
    path(
        "dashboard/administrator/",
        views.administrator_dashboard, # type: ignore
        name="administrator_dashboard",
    ),
    path(
         "student/profile/",
    views.student_profile,
    name="student_profile",
    ),
    path(
        "student/profile/edit/",
    views.edit_student_profile,
    name="edit_student_profile",
    ),
    path(
    "student/course-matches/",
    views.course_matches,
    name="course_matches",
    ),

    path("countries/", views.country_list, name="country_list"),
    path("countries/<int:pk>/", views.country_detail, name="country_detail"),

    path("universities/", views.university_list, name="university_list"),
    path("universities/<int:pk>/", views.university_detail, name="university_detail"),

    path("courses/", views.course_list, name="course_list"),
    path("courses/<int:pk>/", views.course_detail, name="course_detail"),
    path("student/shortlist/", views.my_shortlist, name="my_shortlist"),

    path(
    "student/shortlist/add/<int:course_id>/",
    views.add_to_shortlist,
    name="add_to_shortlist",
    ),
    path(
    "student/shortlist/remove/<int:shortlist_id>/",
    views.remove_from_shortlist,
    name="remove_from_shortlist",
    ),
    path(
    "student/appointments/book/",
    views.book_appointment,
    name="book_appointment",
    ),
    path(
    "student/appointments/",
    views.my_appointments,
    name="my_appointments",
    ),
    
    path(
    "counselor/appointments/",
    views.counselor_appointments,
    name="counselor_appointments",
    ),
    path(
    "counselor/appointments/<int:appointment_id>/status/",
    views.update_appointment_status,
    name="update_appointment_status",
    ),
    
    path(
    "student/appointments/<int:appointment_id>/cancel/",
    views.cancel_appointment,
    name="cancel_appointment",
    ),
    
    path(
    "counselor/availability/",
    views.manage_availability,
    name="manage_availability",
    ),
    path(
    "counselor/availability/<int:slot_id>/toggle/",
    views.toggle_availability,
    name="toggle_availability",
    ),
    path(
    "student/documents/upload/",
    views.upload_student_document,
    name="upload_student_document",
    ),
    path(
    "student/documents/",
    views.my_documents,
    name="my_documents",
    ),
    path(
    "documentation/reviews/",
    views.document_review_queue,
    name="document_review_queue",
    ),
    path(
    "documentation/reviews/<int:document_id>/",
    views.review_student_document,
    name="review_student_document",
    ),
    path(
    "documents/<int:document_id>/download/",
    views.download_student_document,
    name="download_student_document",
    ),
    path(
    "applications/",
    views.my_student_applications,
    name="my_student_applications",
    ),
    path(
    "applications/create/",
    views.create_student_application,
    name="create_student_application",
    ),
    path(
    "applications/<int:application_id>/",
    views.student_application_detail,
    name="student_application_detail",
    ),
    path(
    "applications/<int:application_id>/update-status/",
    views.update_student_application_status,
    name="update_student_application_status",
    ),
    path(
    "applications/<int:application_id>/update-status/page/",
    views.application_status_update_page,
    name="application_status_update_page",
    ),
    path(
    "notifications/",
    views.my_notifications,
    name="my_notifications",
    ),
    path(
    "notifications/<int:notification_id>/mark-read/",
    views.mark_notification_read,
    name="mark_notification_read",
    ),
    
    path(
    "counselor-notes/",
    views.counselor_notes,
    name="counselor_notes",
    ),
    path(
    "counselor-notes/create/",
    views.create_counselor_note,
    name="create_counselor_note",
    ),
    
path(
    "applications/manage/",
    views.application_management,
    name="application_management",
),




]
