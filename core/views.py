from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from accounts.models import User
from .forms import StudentProfileForm
from .models import Country, Course, StudentProfile, University
from .matching import match_courses
from django.views.decorators.http import require_POST
from .models import CourseShortlist
from django.db import IntegrityError, transaction
from django.utils import timezone
from .forms import AppointmentBookingForm
from .models import Appointment
from .forms import CounselorAvailabilityForm
from .models import CounselorAvailability
from core.models import CounselorAvailability
from .forms import StudentDocumentUploadForm
from .models import StudentDocument
from django.http import FileResponse, Http404
from .forms import StudentApplicationForm
from .models import StudentApplication, ApplicationStatusHistory, Notification
from django.core.exceptions import PermissionDenied
from .forms import ApplicationStatusUpdateForm
from .forms import CounselorNoteForm
from .models import CounselorNote







def home(request):
    return render(request, "core/home.html")


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect("core:administrator_dashboard")

    role_dashboards = {
        User.Role.STUDENT: "core:student_dashboard",
        User.Role.COUNSELOR: "core:counselor_dashboard",
        User.Role.DOCUMENTATION_OFFICER: "core:documentation_dashboard",
        User.Role.ADMINISTRATOR: "core:administrator_dashboard",
    }

    return redirect(
        role_dashboards.get(
            request.user.role,
            "core:student_dashboard",
        )
    )


@login_required
def student_dashboard(request):
    if (
        not request.user.is_superuser
        and request.user.role != User.Role.STUDENT
    ):
        return redirect("core:dashboard")

    student = request.user
    now = timezone.now()

    context = {
        "dashboard_title": "Student Dashboard",
        "total_applications": StudentApplication.objects.filter(
            student=student
        ).count(),
        "shortlisted_courses": CourseShortlist.objects.filter(
            student=student
        ).count(),
        "unread_notifications": Notification.objects.filter(
            recipient=student,
            is_read=False,
        ).count(),
        "total_appointments": Appointment.objects.filter(
            student=student
        ).count(),
        "upcoming_appointments": Appointment.objects.filter(
            student=student,
            appointment_datetime__gte=now,
            status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.CONFIRMED,
            ],
        ).count(),
        "recent_applications": StudentApplication.objects.filter(
            student=student
        ).select_related("course").order_by("-created_at")[:5],
        "recent_notifications": Notification.objects.filter(
            recipient=student
        ).order_by("-created_at")[:5],
    }

    return render(request, "core/role_dashboard.html", context)


@login_required
def counselor_dashboard(request):
    if (
        not request.user.is_superuser
        and request.user.role != User.Role.COUNSELOR
    ):
        return redirect("core:dashboard")

    now = timezone.now()

    context = {
        "dashboard_title": "Counselor Dashboard",
        "total_applications": StudentApplication.objects.count(),
        "applications_needing_review": StudentApplication.objects.filter(
            status__in=[
                StudentApplication.Status.SUBMITTED,
                StudentApplication.Status.UNDER_REVIEW,
                StudentApplication.Status.DOCUMENTS_REQUIRED,
            ]
        ).count(),
        "upcoming_appointments": Appointment.objects.filter(
            counselor=request.user,
            appointment_datetime__gte=now,
            status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.CONFIRMED,
            ],
        ).count(),
        "total_counselor_notes": CounselorNote.objects.filter(
            counselor=request.user
        ).count(),
        "recent_applications": StudentApplication.objects.select_related(
            "student", "course"
        ).order_by("-created_at")[:5],
    }

    return render(request, "core/role_dashboard.html", context)


@login_required
def documentation_dashboard(request):
    if (
        not request.user.is_superuser
        and request.user.role != User.Role.DOCUMENTATION_OFFICER
    ):
        return redirect("core:dashboard")

    context = {
        "dashboard_title": "Documentation Officer Dashboard",
        "total_documents": StudentDocument.objects.count(),
        "pending_documents": StudentDocument.objects.filter(
            status=StudentDocument.Status.PENDING
        ).count(),
        "approved_documents": StudentDocument.objects.filter(
            status=StudentDocument.Status.APPROVED
        ).count(),
        "rejected_documents": StudentDocument.objects.filter(
            status=StudentDocument.Status.REJECTED
        ).count(),
    }

    return render(request, "core/role_dashboard.html", context)


@login_required
def administrator_dashboard(request):
    if (
        not request.user.is_superuser
        and request.user.role != User.Role.ADMINISTRATOR
    ):
        return redirect("core:dashboard")

    now = timezone.now()

    context = {
        "dashboard_title": "Administrator Dashboard",
        "total_students": User.objects.filter(
            role=User.Role.STUDENT
        ).count(),
        "total_counselors": User.objects.filter(
            role=User.Role.COUNSELOR
        ).count(),
        "total_applications": StudentApplication.objects.count(),
        "applications_needing_review": StudentApplication.objects.filter(
            status__in=[
                StudentApplication.Status.SUBMITTED,
                StudentApplication.Status.UNDER_REVIEW,
                StudentApplication.Status.DOCUMENTS_REQUIRED,
            ]
        ).count(),
        "total_documents": StudentDocument.objects.count(),
        "pending_documents": StudentDocument.objects.filter(
            status=StudentDocument.Status.PENDING
        ).count(),
        "upcoming_appointments": Appointment.objects.filter(
            appointment_datetime__gte=now,
            status__in=[
                Appointment.Status.PENDING,
                Appointment.Status.CONFIRMED,
            ],
        ).count(),
        "recent_applications": StudentApplication.objects.select_related(
            "student", "course"
        ).order_by("-created_at")[:5],
    }

    return render(request, "core/role_dashboard.html", context)


@login_required
def student_profile(request):
    if not request.user.is_superuser and request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    return render(
        request,
        "core/student_profile.html",
        {"profile": profile},
    )


@login_required
def edit_student_profile(request):
    if not request.user.is_superuser and request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = StudentProfileForm(request.POST, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your student profile has been updated successfully.",
            )
            return redirect("core:student_profile")
    else:
        form = StudentProfileForm(instance=profile)

    return render(
        request,
        "core/edit_student_profile.html",
        {"form": form},
    )


def country_list(request):
    countries = Country.objects.filter(is_active=True)

    query = request.GET.get("q", "").strip()
    if query:
        countries = countries.filter(
            Q(name__icontains=query)
            | Q(official_language__icontains=query)
        )

    return render(
        request,
        "core/country_list.html",
        {"countries": countries, "query": query},
    )


def country_detail(request, pk):
    country = get_object_or_404(
        Country,
        pk=pk,
        is_active=True,
    )
    universities = country.universities.filter(is_active=True) # type: ignore

    return render(
        request,
        "core/country_detail.html",
        {
            "country": country,
            "universities": universities,
        },
    )


def university_list(request):
    universities = University.objects.filter(
        is_active=True,
        country__is_active=True,
    ).select_related("country")

    query = request.GET.get("q", "").strip()
    country_id = request.GET.get("country", "").strip()

    if query:
        universities = universities.filter(
            Q(name__icontains=query)
            | Q(city__icontains=query)
            | Q(country__name__icontains=query)
        )

    if country_id.isdigit():
        universities = universities.filter(country_id=int(country_id))

    countries = Country.objects.filter(is_active=True)

    return render(
        request,
        "core/university_list.html",
        {
            "universities": universities,
            "countries": countries,
            "query": query,
            "selected_country": country_id,
        },
    )


def university_detail(request, pk):
    university = get_object_or_404(
        University.objects.select_related("country"),
        pk=pk,
        is_active=True,
        country__is_active=True,
    )
    courses = university.courses.filter(is_active=True) # type: ignore

    return render(
        request,
        "core/university_detail.html",
        {
            "university": university,
            "courses": courses,
        },
    )


def course_list(request):
    courses = Course.objects.filter(
        is_active=True,
        university__is_active=True,
        university__country__is_active=True,
    ).select_related("university", "university__country")

    query = request.GET.get("q", "").strip()
    study_level = request.GET.get("level", "").strip()
    country_id = request.GET.get("country", "").strip()

    if query:
        courses = courses.filter(
            Q(name__icontains=query)
            | Q(university__name__icontains=query)
            | Q(entry_requirements__icontains=query)
        )

    valid_levels = [
        value for value, label in Course.StudyLevel.choices
    ]
    if study_level in valid_levels:
        courses = courses.filter(study_level=study_level)

    if country_id.isdigit():
        courses = courses.filter(
            university__country_id=int(country_id)
        )

    countries = Country.objects.filter(is_active=True)

    return render(
        request,
        "core/course_list.html",
        {
            "courses": courses,
            "countries": countries,
            "query": query,
            "selected_level": study_level,
            "selected_country": country_id,
            "study_levels": Course.StudyLevel.choices,
        },
    )


def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.select_related(
            "university",
            "university__country",
        ),
        pk=pk,
        is_active=True,
        university__is_active=True,
        university__country__is_active=True,
    )

    return render(
        request,
        "core/course_detail.html",
        {"course": course},
    )

@login_required
def course_matches(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    profile, _ = StudentProfile.objects.get_or_create(
        user=request.user
    )

    results = match_courses(profile)

    return render(
        request,
        "core/course_matches.html",
        {
            "profile": profile,
            "results": results,
        },
    )

@login_required
def my_shortlist(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    shortlist_items = (
        CourseShortlist.objects.filter(student=request.user)
        .select_related(
            "course",
            "course__university",
            "course__university__country",
        )
    )

    return render(
        request,
        "core/my_shortlist.html",
        {"shortlist_items": shortlist_items},
    )


@login_required
@require_POST
def add_to_shortlist(request, course_id):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    course = get_object_or_404(
        Course,
        pk=course_id,
        is_active=True,
        university__is_active=True,
        university__country__is_active=True,
    )

    _, created = CourseShortlist.objects.get_or_create(
        student=request.user,
        course=course,
    )

    if created:
        messages.success(request, "Course added to your shortlist.")
    else:
        messages.info(request, "This course is already in your shortlist.")

    return redirect(request.POST.get("next") or "core:my_shortlist")


@login_required
@require_POST
def remove_from_shortlist(request, shortlist_id):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    item = get_object_or_404(
        CourseShortlist,
        pk=shortlist_id,
        student=request.user,
    )
    item.delete()

    messages.success(request, "Course removed from your shortlist.")
    return redirect("core:my_shortlist")



@login_required
def book_appointment(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = AppointmentBookingForm(request.POST)

        if form.is_valid():
            slot = form.cleaned_data["availability_slot"]

            try:
                with transaction.atomic():
                    # Lock the slot while checking and booking it.
                    slot = CounselorAvailability.objects.select_for_update().get(
                        pk=slot.pk
                    )

                    if (
                        not slot.is_available
                        or slot.start_datetime <= timezone.now()
                        or Appointment.objects.filter(
                            availability_slot=slot,
                        ).exclude(
                            status=Appointment.Status.CANCELLED
                        ).exists()
                    ):
                        form.add_error(
                            "availability_slot",
                            "This slot is no longer available. Please choose another.",
                        )
                    else:
                        appointment = form.save(commit=False)
                        appointment.student = request.user
                        appointment.counselor = slot.counselor
                        appointment.availability_slot = slot
                        appointment.appointment_datetime = slot.start_datetime
                        appointment.save()

                        slot.is_available = False
                        slot.save(update_fields=["is_available"])

            except CounselorAvailability.DoesNotExist:
                form.add_error(
                    "availability_slot",
                    "This slot no longer exists. Please choose another.",
                )
            else:
                if not form.errors:
                    messages.success(
                        request,
                        "Your appointment request was submitted.",
                    )
                    return redirect("core:my_appointments")
    else:
        form = AppointmentBookingForm()

    return render(
        request,
        "core/book_appointment.html",
        {"form": form},
    )


@login_required
def my_appointments(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    appointments = (
        Appointment.objects
        .filter(student=request.user)
        .select_related("counselor")
        .order_by("-appointment_datetime")
    )

    return render(
        request,
        "core/my_appointments.html",
        {"appointments": appointments},
    )


@login_required
def counselor_appointments(request):
    if request.user.role != User.Role.COUNSELOR:
        return redirect("core:dashboard")

    appointments = (
        Appointment.objects
        .filter(counselor=request.user)
        .select_related("student")
        .order_by("appointment_datetime")
    )

    return render(
        request,
        "core/counselor_appointments.html",
        {"appointments": appointments},
    )


@login_required
@require_POST
def update_appointment_status(request, appointment_id):
    if request.user.role != User.Role.COUNSELOR:
        return redirect("core:dashboard")

    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        counselor=request.user,
    )

    new_status = request.POST.get("status")

    allowed_transitions = {
        Appointment.Status.PENDING: {
            Appointment.Status.CONFIRMED,
            Appointment.Status.CANCELLED,
        },
        Appointment.Status.CONFIRMED: {
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
        },
    }

    allowed = allowed_transitions.get(appointment.status, set()) # type: ignore

    if new_status not in allowed:
        messages.error(
            request,
            "That status change is not allowed.",
        )
    else:
        appointment.status = new_status
        appointment.save(update_fields=["status", "updated_at"])
        messages.success(
            request,
            "Appointment status updated successfully.",
        )

    return redirect("core:counselor_appointments")



@login_required
@require_POST
def cancel_appointment(request, appointment_id):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    appointment = get_object_or_404(
        Appointment,
        pk=appointment_id,
        student=request.user,
    )

    if appointment.status not in {
        Appointment.Status.PENDING,
        Appointment.Status.CONFIRMED,
    }:
        messages.error(
            request,
            "This appointment can no longer be cancelled.",
        )
        return redirect("core:my_appointments")

    with transaction.atomic():
        # Re-fetch the appointment inside the transaction.
        appointment = get_object_or_404(
            Appointment.objects.select_for_update(),
            pk=appointment_id,
            student=request.user,
        )

        # Check again in case its status changed.
        if appointment.status not in {
            Appointment.Status.PENDING,
            Appointment.Status.CONFIRMED,
        }:
            messages.error(
                request,
                "This appointment can no longer be cancelled.",
            )
            return redirect("core:my_appointments")

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        # Restore the slot only if it is still in the future
        # and no active appointment uses it.
        if appointment.availability_slot_id: # type: ignore
            slot = (
                CounselorAvailability.objects.select_for_update()
                .filter(pk=appointment.availability_slot_id) # type: ignore
                .first()
            )

            if (
                slot
                and slot.start_datetime > timezone.now()
                and not Appointment.objects.filter(
                    availability_slot=slot
                ).exclude(
                    status=Appointment.Status.CANCELLED
                ).exists()
            ):
                slot.is_available = True
                slot.save(update_fields=["is_available"])

    messages.success(
        request,
        "Your appointment has been cancelled.",
    )
    return redirect("core:my_appointments")

@login_required
def manage_availability(request):
    if request.user.role != User.Role.COUNSELOR:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = CounselorAvailabilityForm(request.POST)

        if form.is_valid():
            slot = form.save(commit=False)
            slot.counselor = request.user
            slot.save()

            messages.success(
                request,
                "Your availability slot has been created.",
            )
            return redirect("core:manage_availability")
    else:
        form = CounselorAvailabilityForm()

    slots = CounselorAvailability.objects.filter(
        counselor=request.user
    ).order_by("start_datetime")

    return render(
        request,
        "core/manage_availability.html",
        {
            "form": form,
            "slots": slots,
            "now": timezone.now(),
        },
    )


@login_required
@require_POST
def toggle_availability(request, slot_id):
    if request.user.role != User.Role.COUNSELOR:
        return redirect("core:dashboard")

    slot = get_object_or_404(
        CounselorAvailability,
        pk=slot_id,
        counselor=request.user,
    )

    if slot.start_datetime <= timezone.now():
        messages.error(
            request,
            "Past or ongoing availability cannot be changed.",
        )
    elif Appointment.objects.filter(
        availability_slot=slot
    ).exclude(
        status=Appointment.Status.CANCELLED
    ).exists():
        messages.error(
            request,
            "This slot has an active appointment and cannot be changed.",
        )
    else:
        slot.is_available = not slot.is_available
        slot.save(update_fields=["is_available"])
        messages.success(request, "Availability updated.")

    return redirect("core:manage_availability")

@login_required
def upload_student_document(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = StudentDocumentUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            document = form.save(commit=False)
            document.student = request.user
            document.save()

            messages.success(
                request,
                "Your document was uploaded successfully.",
            )
            return redirect("core:my_documents")
    else:
        form = StudentDocumentUploadForm()

    return render(
        request,
        "core/upload_student_document.html",
        {"form": form},
    )


@login_required
def my_documents(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    documents = StudentDocument.objects.filter(
        student=request.user
    )

    return render(
        request,
        "core/my_documents.html",
        {"documents": documents},
    )

@login_required
def document_review_queue(request):
    if request.user.role != User.Role.DOCUMENTATION_OFFICER:
        return redirect("core:dashboard")

    documents = StudentDocument.objects.select_related(
        "student"
    ).filter(
        status=StudentDocument.Status.PENDING
    ).order_by("uploaded_at")

    return render(
        request,
        "core/document_review_queue.html",
        {"documents": documents},
    )


@login_required
def review_student_document(request, document_id):
    if request.user.role != User.Role.DOCUMENTATION_OFFICER:
        return redirect("core:dashboard")

    document = get_object_or_404(
        StudentDocument,
        pk=document_id,
    )

    if request.method == "POST":
        if document.status != StudentDocument.Status.PENDING:
            messages.error(
                request,
                "This document has already been reviewed.",
            )
            return redirect("core:document_review_queue")

        decision = request.POST.get("status", "")
        feedback = request.POST.get(
            "review_feedback", ""
        ).strip()

        valid_decisions = {
            StudentDocument.Status.APPROVED,
            StudentDocument.Status.REJECTED,
        }

        if decision not in valid_decisions:
            messages.error(
                request,
                "Please select a valid review decision.",
            )
        elif len(feedback) > 1000:
            messages.error(
                request,
                "Feedback must not exceed 1000 characters.",
            )
        elif (
            decision == StudentDocument.Status.REJECTED
            and not feedback
        ):
            messages.error(
                request,
                "Please explain why the document needs resubmission.",
            )
        else:
            document.status = decision
            document.review_feedback = feedback
            document.reviewed_by = request.user
            document.reviewed_at = timezone.now()
            document.save(
                update_fields=[
                    "status",
                    "review_feedback",
                    "reviewed_by",
                    "reviewed_at",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Document review saved successfully.",
            )
            return redirect("core:document_review_queue")

    return render(
        request,
        "core/review_student_document.html",
        {"document": document},
    )

@login_required
def download_student_document(request, document_id):
    document = get_object_or_404(
        StudentDocument,
        pk=document_id,
    )

    is_owner = (
        request.user.role == User.Role.STUDENT
        and document.student_id == request.user.id # type: ignore
    )

    is_documentation_officer = (
        request.user.role == User.Role.DOCUMENTATION_OFFICER
    )

    if not (is_owner or is_documentation_officer):
        raise Http404("Document not found.")

    if not document.file:
        raise Http404("Document file not found.")

    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.title,
    )

@login_required
def create_student_application(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    if request.method == "POST":
        form = StudentApplicationForm(request.POST)

        if form.is_valid():
            application = form.save(commit=False)
            application.student = request.user
            application.status = StudentApplication.Status.SUBMITTED
            application.save()

            ApplicationStatusHistory.objects.create(
                application=application,
                previous_status="",
                new_status=application.status,
                changed_by=request.user,
                note="Demo application created.",
            )

            messages.success(
                request,
                "Your demo application has been created.",
            )
            return redirect(
                "core:student_application_detail",
                application_id=application.pk,
            )
    else:
        form = StudentApplicationForm()

    return render(
        request,
        "core/create_student_application.html",
        {"form": form},
    )


@login_required
def my_student_applications(request):
    if request.user.role != User.Role.STUDENT:
        return redirect("core:dashboard")

    applications = (
        StudentApplication.objects
        .filter(student=request.user)
        .select_related("course")
    )

    return render(
        request,
        "core/my_student_applications.html",
        {"applications": applications},
    )


@login_required
def student_application_detail(request, application_id):
    if request.user.role == User.Role.STUDENT:
        application_queryset = StudentApplication.objects.filter(
            student=request.user
        )
    elif request.user.role in [
        User.Role.COUNSELOR,
        User.Role.ADMINISTRATOR,
    ]:
        application_queryset = StudentApplication.objects.all()
    else:
        raise PermissionDenied(
            "You are not allowed to view application details."
        )

    application = get_object_or_404(
        application_queryset.select_related("course", "student"),
        pk=application_id,
    )

    history = application.status_history.select_related( # type: ignore
        "changed_by"
    ).all()

    return render(
        request,
        "core/student_application_detail.html",
        {
            "application": application,
            "history": history,
        },
    )



@login_required
def update_student_application_status(request, application_id):
    allowed_roles = [
        User.Role.COUNSELOR,
        User.Role.ADMINISTRATOR,
    ]

    if request.user.role not in allowed_roles:
        raise PermissionDenied(
            "You are not allowed to update application statuses."
        )

    if request.method != "POST":
        return redirect(
            "core:student_application_detail",
            application_id=application_id,
        )

    with transaction.atomic():
        application = get_object_or_404(
            StudentApplication.objects.select_for_update(),
            pk=application_id,
        )

        form = ApplicationStatusUpdateForm(request.POST)

        if form.is_valid():
            new_status = form.cleaned_data["status"]
            note = form.cleaned_data["note"]

            if new_status == application.status:
                messages.info(
                    request,
                    "The application already has this status.",
                )
            else:
                previous_status = application.status

                application.status = new_status
                application.save(update_fields=["status", "updated_at"])

                ApplicationStatusHistory.objects.create(
                    application=application,
                    previous_status=previous_status,
                    new_status=new_status,
                    changed_by=request.user,
                    note=note,
                )
                
                Notification.objects.create(
                    recipient=application.student,
                    application=application,
                    title="Application Status Updated",
                    message=(
                        f"Your application {application.reference_code} "
                        f"status changed to "
                        f"{application.get_status_display()}." # type: ignore
                    ),
                )


                messages.success(
                    request,
                    "Application status updated successfully.",
                )
        else:
            messages.error(
                request,
                "Invalid status update. Please select a valid status.",
            )

    return redirect(
        "core:student_application_detail",
        application_id=application_id,
    )


@login_required
def application_status_update_page(request, application_id):
    allowed_roles = [
        User.Role.COUNSELOR,
        User.Role.ADMINISTRATOR,
    ]

    if request.user.role not in allowed_roles:
        raise PermissionDenied(
            "You are not allowed to update application statuses."
        )

    application = get_object_or_404(
        StudentApplication.objects.select_related(
            "student", "course"
        ),
        pk=application_id,
    )

    form = ApplicationStatusUpdateForm(
        initial={"status": application.status}
    )

    return render(
        request,
        "core/update_application_status.html",
        {
            "application": application,
            "form": form,
        },
    )


@login_required
def my_notifications(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    )

    return render(
        request,
        "core/my_notifications.html",
        {"notifications": notifications},
    )


@login_required
def mark_notification_read(request, notification_id):
    if request.method != "POST":
        return redirect("core:my_notifications")

    notification = get_object_or_404(
        Notification,
        pk=notification_id,
        recipient=request.user,
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    messages.success(request, "Notification marked as read.")
    return redirect("core:my_notifications")


@login_required
def create_counselor_note(request):
    if request.user.role != User.Role.COUNSELOR:
        raise PermissionDenied(
            "Only counselors can create counselor notes."
        )

    if request.method == "POST":
        form = CounselorNoteForm(request.POST)

        if form.is_valid():
            counselor_note = form.save(commit=False)
            counselor_note.counselor = request.user
            counselor_note.save()

            messages.success(
                request,
                "Counselor note saved successfully.",
            )
            return redirect("core:counselor_notes")
    else:
        form = CounselorNoteForm()

    return render(
        request,
        "core/create_counselor_note.html",
        {"form": form},
    )


@login_required
def counselor_notes(request):
    if request.user.role == User.Role.COUNSELOR:
        notes = CounselorNote.objects.filter(
            counselor=request.user
        ).select_related("student", "application")
    elif request.user.role == User.Role.ADMINISTRATOR:
        notes = CounselorNote.objects.select_related(
            "counselor", "student", "application"
        )
    else:
        raise PermissionDenied(
            "You are not allowed to view counselor notes."
        )

    return render(
        request,
        "core/counselor_notes.html",
        {"notes": notes},
    )


@login_required
def application_management(request):
    if request.user.role not in [
        User.Role.COUNSELOR,
        User.Role.ADMINISTRATOR,
    ] and not request.user.is_superuser:
        raise PermissionDenied(
            "Only counselors and administrators can manage applications."
        )

    applications = StudentApplication.objects.select_related(
        "student",
        "course",
        "course__university",
    ).order_by("-created_at")

    return render(
        request,
        "core/application_management.html",
        {"applications": applications},
    )
