
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from .models import Notification, StudentProfile, Country
from core.models import Country, University, Course, StudentProfile
from core.matching import match_courses
from core.models import CourseShortlist
from .models import Appointment,CounselorAvailability
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import StudentDocument, StudentApplication
from django.utils import timezone
from datetime import timedelta
from core.models import (
    StudentApplication,
    ApplicationStatusHistory,
    CounselorNote,
)


class DashboardAccessTests(TestCase):
    def create_user(self, username, role):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="StrongTestPass!827",
            role=role,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_student_can_access_student_dashboard(self):
        user = self.create_user("student01", User.Role.STUDENT)
        self.client.force_login(user)

        response = self.client.get(
            reverse("core:student_dashboard")
        )
        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_counselor_dashboard(self):
        user = self.create_user("student02", User.Role.STUDENT)
        self.client.force_login(user)

        response = self.client.get(
            reverse("core:counselor_dashboard")
        )
        self.assertEqual(response.status_code, 302)

    def test_counselor_can_access_counselor_dashboard(self):
        user = self.create_user("counselor01", User.Role.COUNSELOR)
        self.client.force_login(user)

        response = self.client.get(
            reverse("core:counselor_dashboard")
        )
        self.assertEqual(response.status_code, 200)


class StudentProfileTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="profile_student",
            email="profile@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )
        self.client.force_login(self.student)

    def test_student_profile_is_created_automatically(self):
        self.assertTrue(
            StudentProfile.objects.filter(user=self.student).exists()
        )

    def test_student_can_view_own_profile(self):
        response = self.client.get(
            reverse("core:student_profile")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "core/student_profile.html"
        )

    def test_student_can_update_profile(self):
        response = self.client.post(
            reverse("core:edit_student_profile"),
            {
                "phone": "9800000000",
                "address": "Kathmandu, Nepal",
                "highest_qualification": "+2 Science",
                "academic_score": "78.50",
                "preferred_study_level": "bachelors",
                "preferred_country": "",
                "annual_budget": "12000",
                "date_of_birth": "",
            },
        )

        self.assertRedirects(
            response, reverse("core:student_profile")
        )

        profile = StudentProfile.objects.get(user=self.student)
        self.assertEqual(profile.phone, "9800000000")
        self.assertEqual(
            profile.highest_qualification, "+2 Science"
        )
        self.assertEqual(
            str(profile.academic_score), "78.50"
        )

    def test_non_student_cannot_access_student_profile(self):
        counselor = User.objects.create_user(
            username="profile_counselor",
            email="counselor_profile@example.com",
            password="TestPass123!",
            role=User.Role.COUNSELOR,
        )
        self.client.force_login(counselor)

        response = self.client.get(
            reverse("core:student_profile")
        )

        # A counselor must not be allowed to view the student profile.
        self.assertEqual(response.status_code, 302)

        # The first redirect should lead to the dashboard router.
        self.assertEqual(
            response.headers["Location"],
            reverse("core:dashboard"),
        )

class CourseMatchingTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="matching_student",
            email="matching@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )

        self.profile = StudentProfile.objects.get(
            user=self.student
        )
        self.country = Country.objects.create(
            name="Demo Australia",
            currency="AUD",
            official_language="English",
            is_active=True,
        )
        self.university = University.objects.create(
            country=self.country,
            name="Demo University",
            city="Demo City",
            is_active=True,
        )
        self.course = Course.objects.create(
            university=self.university,
            name="Bachelor of Information Technology",
            study_level="bachelors",
            duration_years=Decimal("3.0"),
            annual_tuition_fee=Decimal("15000.00"),
            currency="AUD",
            minimum_academic_score=Decimal("65.00"),
            is_active=True,
        )

        self.profile.academic_score = Decimal("75.00")
        self.profile.preferred_study_level = "bachelors"
        
        self.profile.preferred_country = self.country # type: ignore

        self.profile.annual_budget = Decimal("20000.00")
        self.profile.annual_budget_currency = "AUD"
        self.profile.save()

    def test_course_matching_all_criteria(self):
        results = match_courses(self.profile)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "matches")
        self.assertEqual(len(results[0]["reasons"]), 4)

    def test_academic_score_below_minimum_needs_review(self):
        self.profile.academic_score = Decimal("55.00")
        self.profile.save()

        results = match_courses(self.profile)

        self.assertEqual(results[0]["status"], "needs_review")
        self.assertTrue(results[0]["concerns"])

    def test_different_budget_currency_is_not_compared(self):
        self.profile.annual_budget_currency = "USD"
        self.profile.annual_budget = Decimal("50000.00")
        self.profile.save()

        results = match_courses(self.profile)

        self.assertIn(
            "Budget and tuition currencies differ; no conversion was applied.",
            results[0]["unknowns"],
        )
        self.assertEqual(results[0]["status"], "insufficient_data")

    def test_missing_academic_score_is_reported(self):
        self.profile.academic_score = None
        self.profile.save()

        results = match_courses(self.profile)

        self.assertIn(
            "Your academic score has not been provided.",
            results[0]["unknowns"],
        )
        self.assertEqual(
            results[0]["status"],
            "insufficient_data",
        )

    def test_inactive_courses_are_excluded(self):
        self.course.is_active = False
        self.course.save()

        results = match_courses(self.profile)

        self.assertEqual(results, [])

    def test_matching_page_requires_login(self):
        response = self.client.get(
            reverse("core:course_matches")
        )

        self.assertEqual(response.status_code, 302)

    def test_student_can_view_matching_page(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("core:course_matches")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "core/course_matches.html",
        )

    def test_counselor_cannot_access_matching_page(self):
        counselor = User.objects.create_user(
            username="matching_counselor",
            password="TestPass123!",
            role=User.Role.COUNSELOR,
        )
        self.client.force_login(counselor)

        response = self.client.get(
            reverse("core:course_matches")
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
    response,
    reverse("core:dashboard"),
    fetch_redirect_response=False,
)

class CourseShortlistTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="shortlist_student",
            email="shortlist@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )
        self.other_student = User.objects.create_user(
            username="other_student",
            email="other@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )
        self.country = Country.objects.create(
            name="Shortlist Test Country",
            currency="AUD",
            is_active=True,
        )
        self.university = University.objects.create(
            country=self.country,
            name="Shortlist Test University",
            is_active=True,
        )
        self.course = Course.objects.create(
            university=self.university,
            name="Shortlist Test Course",
            study_level="bachelors",
            duration_years=Decimal("3.0"),
            annual_tuition_fee=Decimal("15000.00"),
            currency="AUD",
            is_active=True,
        )

    def test_student_can_view_own_shortlist(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("core:my_shortlist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "core/my_shortlist.html"
        )

    def test_student_can_add_course(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:add_to_shortlist",
                args=[self.course.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            CourseShortlist.objects.filter(
                student=self.student,
                course=self.course,
            ).exists()
        )

    def test_duplicate_shortlist_entry_is_prevented(self):
        self.client.force_login(self.student)

        url = reverse(
            "core:add_to_shortlist",
            args=[self.course.pk],
        )
        self.client.post(url)
        self.client.post(url)

        self.assertEqual(
            CourseShortlist.objects.filter(
                student=self.student,
                course=self.course,
            ).count(),
            1,
        )

    def test_student_cannot_remove_another_students_entry(self):
        item = CourseShortlist.objects.create(
            student=self.other_student,
            course=self.course,
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:remove_from_shortlist",
                args=[item.pk],
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            CourseShortlist.objects.filter(pk=item.pk).exists()
        )

    def test_student_can_remove_own_entry(self):
        item = CourseShortlist.objects.create(
            student=self.student,
            course=self.course,
        )
        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:remove_from_shortlist",
                args=[item.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            CourseShortlist.objects.filter(pk=item.pk).exists()
        )

    def test_add_to_shortlist_requires_login(self):
        response = self.client.post(
            reverse(
                "core:add_to_shortlist",
                args=[self.course.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(CourseShortlist.objects.exists())

class AppointmentBookingTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone

        self.student = User.objects.create_user(
            username="appointment_student",
            email="appointment_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )

        self.counselor = User.objects.create_user(
            username="appointment_counselor",
            email="appointment_counselor@example.com",
            password="TestPass123!",
            role=User.Role.COUNSELOR,
        )

        start = timezone.now() + timedelta(days=2)
        start = start.replace(second=0, microsecond=0)

        self.slot = CounselorAvailability.objects.create(
            counselor=self.counselor,
            start_datetime=start,
            end_datetime=start + timedelta(minutes=30),
            is_available=True,
        )

    def test_student_can_book_available_slot(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("core:book_appointment"),
            {
                "availability_slot": self.slot.pk,
                "reason": "I need course selection guidance.",
            },
        )

        self.assertRedirects(
            response,
            reverse("core:my_appointments"),
        )

        appointment = Appointment.objects.get(student=self.student)

        self.assertEqual(appointment.counselor, self.counselor)
        self.assertEqual(appointment.availability_slot, self.slot)
        self.assertEqual(
            appointment.appointment_datetime,
            self.slot.start_datetime,
        )
        self.assertFalse(
            CounselorAvailability.objects.get(pk=self.slot.pk).is_available
        )

    def test_counselor_cannot_book_as_student(self):
        self.client.force_login(self.counselor)

        response = self.client.post(
        reverse("core:book_appointment"),
        {
            "availability_slot": self.slot.pk,
            "reason": "Test booking",
        },
    )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
        response.url, # type: ignore
        reverse("core:dashboard"),
    )
        self.assertFalse(Appointment.objects.exists())

    def test_unavailable_slot_cannot_be_booked(self):
        self.slot.is_available = False
        self.slot.save(update_fields=["is_available"])

        self.client.force_login(self.student)

        response = self.client.post(
            reverse("core:book_appointment"),
            {
                "availability_slot": self.slot.pk,
                "reason": "Test booking",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Appointment.objects.exists())

    def test_student_cannot_cancel_another_students_appointment(self):
        other_student = User.objects.create_user(
            username="other_appointment_student",
            email="other_appointment_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )

        appointment = Appointment.objects.create(
            student=other_student,
            counselor=self.counselor,
            availability_slot=self.slot,
            appointment_datetime=self.slot.start_datetime,
            reason="Private consultation",
            status=Appointment.Status.PENDING,
        )

        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:cancel_appointment",
                args=[appointment.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

        appointment.refresh_from_db()
        self.assertEqual(
            appointment.status,
            Appointment.Status.PENDING,
        )

    
    
    def test_student_can_cancel_own_pending_appointment(self):
        self.slot.is_available = False
        self.slot.save(update_fields=["is_available"])

        appointment = Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            availability_slot=self.slot,
            appointment_datetime=self.slot.start_datetime,
            reason="Course guidance",
            status=Appointment.Status.PENDING,
        )

        self.client.force_login(self.student)

        response = self.client.post(
            reverse("core:cancel_appointment", args=[appointment.pk])
        )

        self.assertRedirects(
            response,
            reverse("core:my_appointments"),
        )

        appointment.refresh_from_db()
        self.slot.refresh_from_db()

        self.assertEqual(
            appointment.status,
            Appointment.Status.CANCELLED,
        )
        self.assertTrue(self.slot.is_available)

class CounselorAvailabilityTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone

        self.counselor = User.objects.create_user(
            username="availability_counselor",
            email="availability_counselor@example.com",
            password="TestPass123!",
            role=User.Role.COUNSELOR,
        )

        self.student = User.objects.create_user(
            username="availability_student",
            email="availability_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )

        start = (timezone.now() + timedelta(days=2)).replace(
            second=0,
            microsecond=0,
        )

        self.slot = CounselorAvailability.objects.create(
            counselor=self.counselor,
            start_datetime=start,
            end_datetime=start + timedelta(minutes=30),
            is_available=False,
        )

    def test_counselor_cannot_toggle_slot_with_active_appointment(self):
        Appointment.objects.create(
            student=self.student,
            counselor=self.counselor,
            availability_slot=self.slot,
            appointment_datetime=self.slot.start_datetime,
            reason="Course guidance",
            status=Appointment.Status.CONFIRMED,
        )

        self.client.force_login(self.counselor)

        response = self.client.post(
            reverse(
                "core:toggle_availability",
                args=[self.slot.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("core:manage_availability"),
        )

        self.slot.refresh_from_db()
        self.assertFalse(self.slot.is_available)

class StudentDocumentTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="document_student",
            email="document_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )

        self.other_student = User.objects.create_user(
            username="other_document_student",
            email="other_document_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )

        self.counselor = User.objects.create_user(
            username="document_counselor",
            email="document_counselor@example.com",
            password="TestPass123!",
            role=User.Role.COUNSELOR,
        )

    def test_student_document_page_requires_login(self):
        response = self.client.get(
            reverse("core:my_documents")
        )
        self.assertEqual(response.status_code, 302)

    def test_student_can_view_own_document_page(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("core:my_documents")
        )

        self.assertEqual(response.status_code, 200)

    def test_counselor_cannot_view_student_document_page(self):
        self.client.force_login(self.counselor)

        response = self.client.get(
            reverse("core:my_documents")
        )

        self.assertEqual(response.status_code, 302)

    def test_student_can_upload_a_pdf(self):
        self.client.force_login(self.student)

        uploaded_file = SimpleUploadedFile(
            "transcript.pdf",
            b"%PDF-1.4 demo file content",
            content_type="application/pdf",
        )

        response = self.client.post(
            reverse("core:upload_student_document"),
            {
                "document_type": "academic_transcript",
                "title": "Academic Transcript",
                "file": uploaded_file,
            },
        )

        self.assertRedirects(
            response,
            reverse("core:my_documents"),
        )

        document = StudentDocument.objects.get(
            student=self.student
        )

        self.assertEqual(
            document.status,
            StudentDocument.Status.PENDING,
        )
        self.assertEqual(document.title, "Academic Transcript")

    def test_student_cannot_upload_an_executable_extension(self):
        self.client.force_login(self.student)

        uploaded_file = SimpleUploadedFile(
            "document.exe",
            b"demo executable content",
            content_type="application/octet-stream",
        )

        response = self.client.post(
            reverse("core:upload_student_document"),
            {
                "document_type": "other",
                "title": "Invalid document",
                "file": uploaded_file,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            StudentDocument.objects.filter(
                student=self.student
            ).exists()
        )

class DocumentReviewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="review_student",
            email="review_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )

        self.officer = User.objects.create_user(
            username="review_officer",
            email="review_officer@example.com",
            password="TestPass123!",
            role=User.Role.DOCUMENTATION_OFFICER,
        )

        self.counselor = User.objects.create_user(
            username="review_counselor",
            email="review_counselor@example.com",
            password="TestPass123!",
            role=User.Role.COUNSELOR,
        )

        self.document = StudentDocument.objects.create(
            student=self.student,
            document_type=StudentDocument.DocumentType.OTHER,
            title="Sample Document",
            file=SimpleUploadedFile(
                "sample.pdf",
                b"%PDF-1.4 test fixture",
                content_type="application/pdf",
            ),
        )

    def test_document_review_queue_requires_officer_role(self):
        self.client.force_login(self.counselor)

        response = self.client.get(
            reverse("core:document_review_queue")
        )

        self.assertEqual(response.status_code, 302)

    def test_officer_can_view_pending_review_queue(self):
        self.client.force_login(self.officer)

        response = self.client.get(
            reverse("core:document_review_queue")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sample Document")

    def test_officer_can_approve_document(self):
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse(
                "core:review_student_document",
                args=[self.document.pk],
            ),
            {
                "status": StudentDocument.Status.APPROVED,
                "review_feedback": "Reviewed for the demo.",
            },
        )

        self.assertRedirects(
            response,
            reverse("core:document_review_queue"),
        )

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            StudentDocument.Status.APPROVED,
        )
        self.assertEqual(self.document.reviewed_by, self.officer)
        self.assertIsNotNone(self.document.reviewed_at)

    def test_rejection_requires_feedback(self):
        self.client.force_login(self.officer)

        response = self.client.post(
            reverse(
                "core:review_student_document",
                args=[self.document.pk],
            ),
            {
                "status": StudentDocument.Status.REJECTED,
                "review_feedback": "",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            StudentDocument.Status.PENDING,
        )
        self.assertIsNone(self.document.reviewed_by)

    def test_student_cannot_review_document(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:review_student_document",
                args=[self.document.pk],
            ),
            {
                "status": StudentDocument.Status.APPROVED,
                "review_feedback": "Attempted review.",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.status,
            StudentDocument.Status.PENDING,
        )

class StudentApplicationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username="app_student",
            email="app_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )
        cls.other_student = User.objects.create_user(
            username="other_app_student",
            email="other_student@example.com",
            password="TestPass123!",
            role=User.Role.STUDENT,
        )
        cls.counselor = User.objects.create_user(
            username="app_counselor",
            email="app_counselor@example.com",
            password="TestPass123!",
            role=User.Role.COUNSELOR,
        )

        # Adapt these fields if your existing models differ.
        cls.country = Country.objects.create(name="Demo Country")
        cls.university = University.objects.create(
            name="Demo University",
            country=cls.country,
        )
        cls.course = Course.objects.create(
            name="Demo Course",
            university=cls.university,
            study_level="bachelor",
            duration_years=3,
            annual_tuition_fee=10000,
        )
        cls.application = StudentApplication.objects.create(
            student=cls.student,
            course=cls.course,
            status=StudentApplication.Status.SUBMITTED,
            student_statement="This is a test application.",
        )

    def test_student_can_open_application_list(self):
        self.client.login(
            username="app_student",
            password="TestPass123!",
        )
        response = self.client.get(
            reverse("core:my_student_applications")
        )
        self.assertEqual(response.status_code, 200)

    def test_counselor_cannot_open_student_application_list(self):
        self.client.login(
            username="app_counselor",
            password="TestPass123!",
        )
        response = self.client.get(
            reverse("core:my_student_applications")
        )
        self.assertEqual(response.status_code, 302)

    def test_student_can_create_application(self):
        self.client.login(
            username="app_student",
            password="TestPass123!",
        )
        response = self.client.post(
            reverse("core:create_student_application"),
            {
                "course": self.course.pk,
                "student_statement": "My study goals.",
            },
        )

        self.assertEqual(response.status_code, 302)
        application = StudentApplication.objects.filter(
            student=self.student,
            course=self.course,
        ).latest("created_at")

        self.assertEqual(
            application.status,
            StudentApplication.Status.SUBMITTED,
        )
        self.assertTrue(application.reference_code)
        self.assertTrue(
            ApplicationStatusHistory.objects.filter(
                application=application,
                new_status=StudentApplication.Status.SUBMITTED,
            ).exists()
        )

    def test_student_cannot_view_another_students_application(self):
        application = StudentApplication.objects.create(
            student=self.other_student,
            course=self.course,
        )
        self.client.login(
            username="app_student",
            password="TestPass123!",
        )

        response = self.client.get(
            reverse(
                "core:student_application_detail",
                args=[application.pk],
            )
        )
        self.assertEqual(response.status_code, 404)
        
    def test_student_cannot_update_application_status(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:update_student_application_status",
                args=[self.application.pk], # type: ignore
            ),
            {
                "status": StudentApplication.Status.UNDER_REVIEW,
                "note": "Review started.",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.application.refresh_from_db() # type: ignore
        self.assertEqual(
            self.application.status, # type: ignore
            StudentApplication.Status.SUBMITTED,
        )

    def test_counselor_can_update_application_status(self):
        self.client.force_login(self.counselor)

        response = self.client.post(
            reverse(
                "core:update_student_application_status",
                args=[self.application.pk], # type: ignore
            ),
            {
                "status": StudentApplication.Status.UNDER_REVIEW,
                "note": "Review started.",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "core:student_application_detail",
                args=[self.application.pk], # type: ignore
            ),
        )

        self.application.refresh_from_db() # type: ignore
        self.assertEqual(
            self.application.status, # type: ignore
            StudentApplication.Status.UNDER_REVIEW,
        )

        history = self.application.status_history.latest( # type: ignore
            "changed_at"
        )
        self.assertEqual(
            history.previous_status,
            StudentApplication.Status.SUBMITTED,
        )
        self.assertEqual(
            history.new_status,
            StudentApplication.Status.UNDER_REVIEW,
        )
        self.assertEqual(history.changed_by, self.counselor)
        self.assertEqual(history.note, "Review started.")
    
    def test_same_status_does_not_create_duplicate_history(self):
        self.client.force_login(self.counselor)

        initial_history_count = (
            self.application.status_history.count() # type: ignore
        )

        response = self.client.post(
            reverse(
                "core:update_student_application_status",
                args=[self.application.pk],
            ),
            {
                "status": StudentApplication.Status.SUBMITTED,
                "note": "No change in status.",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.application.refresh_from_db()

        self.assertEqual(
            self.application.status,
            StudentApplication.Status.SUBMITTED,
        )
        self.assertEqual(
            self.application.status_history.count(), # type: ignore
            initial_history_count,
        )

    
    def test_documentation_officer_cannot_update_status(self):
        officer = User.objects.create_user(
            username="test_doc_officer",
            email="doc_officer@example.com",
            password="TestPassword123!",
            role=User.Role.DOCUMENTATION_OFFICER,
        )

        self.client.force_login(officer)

        response = self.client.post(
            reverse(
                "core:update_student_application_status",
                args=[self.application.pk],
            ),
            {
                "status": StudentApplication.Status.UNDER_REVIEW,
                "note": "Unauthorized update attempt.",
            },
        )

        self.assertEqual(response.status_code, 403)

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            StudentApplication.Status.SUBMITTED,
        )
    
    def test_student_sees_only_own_notifications(self):
        own_notification = Notification.objects.create(
            recipient=self.student,
            application=self.application,
            title="My update",
            message="Your application is under review.",
        )

        other_notification = Notification.objects.create(
            recipient=self.other_student,
            title="Private update",
            message="This belongs to another student.",
        )

        self.client.force_login(self.student)

        response = self.client.get(
            reverse("core:my_notifications")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My update")
        self.assertNotContains(response, "Private update")
        self.assertQuerySetEqual(
            response.context["notifications"],
            [own_notification],
        )

    def test_student_can_mark_own_notification_as_read(self):
        notification = Notification.objects.create(
            recipient=self.student,
            application=self.application,
            title="Status update",
            message="Your application status changed.",
        )

        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:mark_notification_read",
                args=[notification.pk],
            )
        )

        self.assertRedirects(
            response,
            reverse("core:my_notifications"),
        )

        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_student_cannot_mark_another_students_notification_read(self):
        notification = Notification.objects.create(
            recipient=self.other_student,
            title="Private update",
            message="Another student's notification.",
        )

        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "core:mark_notification_read",
                args=[notification.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

        notification.refresh_from_db()
        self.assertFalse(notification.is_read)


class CounselorNoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user(
            username="note_student",
            email="note_student@example.com",
            password="TestPassword123!",
            role=User.Role.STUDENT,
        )
        cls.other_student = User.objects.create_user(
            username="note_other_student",
            email="note_other_student@example.com",
            password="TestPassword123!",
            role=User.Role.STUDENT,
        )
        cls.counselor = User.objects.create_user(
            username="note_counselor",
            email="note_counselor@example.com",
            password="TestPassword123!",
            role=User.Role.COUNSELOR,
        )
        cls.other_counselor = User.objects.create_user(
            username="note_other_counselor",
            email="note_other_counselor@example.com",
            password="TestPassword123!",
            role=User.Role.COUNSELOR,
        )
        cls.admin = User.objects.create_user(
            username="note_admin",
            email="note_admin@example.com",
            password="TestPassword123!",
            role=User.Role.ADMINISTRATOR,
        )

        cls.note = CounselorNote.objects.create(
            counselor=cls.counselor,
            student=cls.student,
            title="Academic guidance",
            note="Discussed study options and next steps.",
        )
        cls.other_note = CounselorNote.objects.create(
            counselor=cls.other_counselor,
            student=cls.other_student,
            title="Document follow-up",
            note="Review the outstanding documents.",
        )

    def test_counselor_can_view_own_notes(self):
        self.client.force_login(self.counselor)

        response = self.client.get(
            reverse("core:counselor_notes")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Academic guidance")
        self.assertNotContains(response, "Document follow-up")

    def test_administrator_can_view_all_notes(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("core:counselor_notes")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Academic guidance")
        self.assertContains(response, "Document follow-up")

    def test_student_cannot_view_counselor_notes(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("core:counselor_notes")
        )

        self.assertEqual(response.status_code, 403)

    def test_documentation_officer_cannot_view_counselor_notes(self):
        officer = User.objects.create_user(
            username="note_officer",
            email="note_officer@example.com",
            password="TestPassword123!",
            role=User.Role.DOCUMENTATION_OFFICER,
        )
        self.client.force_login(officer)

        response = self.client.get(
            reverse("core:counselor_notes")
        )

        self.assertEqual(response.status_code, 403)

    def test_counselor_can_create_note(self):
        self.client.force_login(self.counselor)

        response = self.client.post(
            reverse("core:create_counselor_note"),
            {
                "student": self.student.pk,
                "application": "",
                "title": "New guidance session",
                "note": "Discussed suitable study pathways.",
            },
        )

        self.assertRedirects(
            response,
            reverse("core:counselor_notes"),
        )
        self.assertTrue(
            CounselorNote.objects.filter(
                counselor=self.counselor,
                student=self.student,
                title="New guidance session",
            ).exists()
        )

    def test_student_cannot_create_counselor_note(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("core:create_counselor_note")
        )

        self.assertEqual(response.status_code, 403)
