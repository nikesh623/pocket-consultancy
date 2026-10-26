from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class StudentProfile(models.Model):
    class StudyLevel(models.TextChoices):
        BACHELORS = "bachelors", "Bachelor's"
        MASTERS = "masters", "Master's"
        PHD = "phd", "PhD"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        limit_choices_to={"role": "student"},
    )
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)

    highest_qualification = models.CharField(max_length=150, blank=True)
    academic_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        help_text="Enter a percentage from 0 to 100.",
    )

    preferred_study_level = models.CharField(
        max_length=20,
        choices=StudyLevel.choices,
        blank=True,
    )
    preferred_country = models.ForeignKey(
        "Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interested_students",
    )
    annual_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Indicative annual budget in your selected planning currency.",
    )

    annual_budget_currency = models.CharField(
        max_length=10,
        default="USD",
        help_text="Currency code for the annual budget, e.g. USD, GBP, AUD.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)
    currency = models.CharField(max_length=50, blank=True)
    official_language = models.CharField(max_length=100, blank=True)
    general_information = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name


class University(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.PROTECT,
        related_name="universities",
    )
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["country", "name"],
                name="unique_university_per_country",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.country.name})"


class Course(models.Model):
    class StudyLevel(models.TextChoices):
        BACHELORS = "bachelors", "Bachelor's"
        MASTERS = "masters", "Master's"
        PHD = "phd", "PhD"

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name="courses",
    )
    name = models.CharField(max_length=200)
    study_level = models.CharField(
        max_length=20,
        choices=StudyLevel.choices,
    )
    duration_years = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(0.5)],
    )
    annual_tuition_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    currency = models.CharField(
        max_length=10,
        default="USD",
        help_text="Currency code for the tuition fee, e.g. USD, GBP, AUD.",
    )
    minimum_academic_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
        help_text="Indicative minimum percentage, from 0 to 100.",
    )
    entry_requirements = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["university", "name", "study_level"],
                name="unique_course_per_university_level",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class CourseShortlist(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="course_shortlists",
        limit_choices_to={"role": "student"},
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="shortlisted_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "course"],
                name="unique_student_course_shortlist",
            )
        ]

    def __str__(self):
        return f"{self.student.username} - {self.course.name}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_appointments",
        limit_choices_to={"role": "student"},
    )

    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="counselor_appointments",
        limit_choices_to={"role": "counselor"},
    )
    
    availability_slot = models.ForeignKey(
    "core.CounselorAvailability",
    on_delete=models.PROTECT,
    related_name="appointments",
    null=True,
    blank=True,
    )


    appointment_datetime = models.DateTimeField()

    reason = models.TextField(max_length=1000)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["appointment_datetime"]
        constraints = [
            models.UniqueConstraint(
                fields=["counselor", "appointment_datetime"],
                condition=~models.Q(status="cancelled"),
                name="unique_active_counselor_appointment",
            )
        ]

    def __str__(self):
        return (
            f"{self.student.username} - "
            f"{self.counselor.username} - "
            f"{self.appointment_datetime}"
        )

class CounselorAvailability(models.Model):
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="availability_slots",
        limit_choices_to={"role": "counselor"},
    )

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()

    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_datetime"]
        constraints = [
            models.UniqueConstraint(
                fields=["counselor", "start_datetime"],
                name="unique_counselor_availability_start",
            ),
        ]
    
    def clean(self):
        from django.core.exceptions import ValidationError

        if self.end_datetime <= self.start_datetime:
            raise ValidationError(
                "The end time must be later than the start time."
            )

    def __str__(self):
        return (
            f"{self.counselor.username}: "
            f"{self.start_datetime} - {self.end_datetime}"
        )

class StudentDocument(models.Model):
    class DocumentType(models.TextChoices):
        ACADEMIC_TRANSCRIPT = "academic_transcript", "Academic Transcript"
        CERTIFICATE = "certificate", "Academic Certificate"
        PASSPORT = "passport", "Passport"
        ENGLISH_TEST = "english_test", "English Test Result"
        FINANCIAL_PROOF = "financial_proof", "Financial Proof"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved for Demo"
        REJECTED = "rejected", "Rejected / Resubmission Required"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_documents",
        limit_choices_to={"role": "student"},
    )

    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
    )

    title = models.CharField(max_length=150)

    file = models.FileField(
        upload_to="student_documents/%Y/%m/",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    review_feedback = models.TextField(
        blank=True,
        max_length=1000,
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_student_documents",
        limit_choices_to={"role": "documentation_officer"},
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.student.username} - {self.title}"



import uuid

# Add these models below your existing models.

class StudentApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        DOCUMENTS_REQUIRED = "documents_required", "Documents Required"
        SHORTLISTED = "shortlisted", "Shortlisted"
        OFFER_RECEIVED = "offer_received", "Offer Received"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_applications",
        limit_choices_to={"role": "student"},
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="student_applications",
    )

    reference_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.SUBMITTED,
    )

    student_statement = models.TextField(blank=True, max_length=2000)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = (
                f"PC-{uuid.uuid4().hex[:12].upper()}"
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference_code} - {self.student.username}"


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        StudentApplication,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    previous_status = models.CharField(
        max_length=30,
        choices=StudentApplication.Status.choices,
        blank=True,
    )

    new_status = models.CharField(
        max_length=30,
        choices=StudentApplication.Status.choices,
    )

    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="application_status_changes",
    )

    note = models.CharField(max_length=1000, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at", "id"]

    def __str__(self):
        return (
            f"{self.application.reference_code}: "
            f"{self.new_status}"
        )


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    application = models.ForeignKey(
        StudentApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    title = models.CharField(max_length=150)
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.recipient.username}"


class CounselorNote(models.Model):
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="counselor_notes",
        limit_choices_to={"role": "counselor"},
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_counselor_notes",
        limit_choices_to={"role": "student"},
    )
    application = models.ForeignKey(
        StudentApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counselor_notes",
    )
    title = models.CharField(max_length=150)
    note = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.student.username}"
