
from django import forms
from .models import StudentProfile
from django.utils import timezone
from accounts.models import User
from .models import Appointment
from .models import CounselorAvailability
from .models import Appointment, CounselorAvailability
from .models import StudentDocument
from .models import StudentApplication, Course
from .models import CounselorNote



class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "date_of_birth",
            "phone",
            "address",
            "highest_qualification",
            "academic_score",
            "preferred_study_level",
            "preferred_country",
            "annual_budget",
        ]

        widgets = {
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone number"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Address"}
            ),
            "highest_qualification": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. +2 Science",
                }
            ),
            "academic_score": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Percentage from 0 to 100",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),
            "preferred_study_level": forms.Select(
                attrs={"class": "form-control"}
            ),
            "preferred_country": forms.Select(
                attrs={"class": "form-control"}
            ),
            "annual_budget": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Annual budget",
                    "min": "0",
                    "step": "0.01",
                }     
            ),
            
            "annual_budget_currency": forms.Select(
                choices=[
                    ("USD", "USD - US Dollar"),
                    ("GBP", "GBP - British Pound"),
                    ("AUD", "AUD - Australian Dollar"),
                    ("CAD", "CAD - Canadian Dollar"),
                    ("EUR", "EUR - Euro"),
                    ("NPR", "NPR - Nepalese Rupee"),
                ],
                attrs={"class": "form-control"},
            ),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preferred_country"].queryset = ( # type: ignore
            self.fields["preferred_country"]
            .queryset.filter(is_active=True) # type: ignore
        )



class AppointmentBookingForm(forms.ModelForm):
    availability_slot = forms.ModelChoiceField(
        queryset=CounselorAvailability.objects.none(),
        empty_label="Choose an available appointment slot",
        label="Available appointment",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Appointment
        fields = ["availability_slot", "reason"]

        widgets = {
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Explain what guidance you need.",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["availability_slot"].queryset = ( # type: ignore
            CounselorAvailability.objects.filter(
                is_available=True,
                start_datetime__gt=timezone.now(),
                counselor__is_active=True,
                counselor__role=User.Role.COUNSELOR,
            )
            .select_related("counselor")
            .order_by("start_datetime")
        )

    def clean_availability_slot(self):
        slot = self.cleaned_data["availability_slot"]

        if not slot.is_available:
            raise forms.ValidationError(
                "This slot is no longer available."
            )

        if slot.start_datetime <= timezone.now():
            raise forms.ValidationError(
                "Choose a future appointment slot."
            )

        if not slot.counselor.is_active:
            raise forms.ValidationError(
                "This counselor is currently unavailable."
            )

        already_booked = Appointment.objects.filter(
            availability_slot=slot,
        ).exclude(status=Appointment.Status.CANCELLED).exists()

        if already_booked:
            raise forms.ValidationError(
                "This slot has already been booked."
            )

        return slot

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()

        if not reason:
            raise forms.ValidationError(
                "Please explain the reason for your consultation."
            )

        return reason



class CounselorAvailabilityForm(forms.ModelForm):
    class Meta:
        model = CounselorAvailability
        fields = ["start_datetime", "end_datetime"]

        widgets = {
            "start_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                },
                format="%Y-%m-%dT%H:%M",
            ),
            "end_datetime": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                },
                format="%Y-%m-%dT%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        date_format = "%Y-%m-%dT%H:%M"
        self.fields["start_datetime"].input_formats = [date_format] # type: ignore
        self.fields["end_datetime"].input_formats = [date_format] # type: ignore

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get("start_datetime")
        end = cleaned_data.get("end_datetime")

        if start and end:
            if end <= start:
                raise forms.ValidationError(
                    "End time must be later than start time."
                )

            if start <= timezone.now():
                self.add_error(
                    "start_datetime",
                    "Availability must start in the future.",
                )

        return cleaned_data

    
class StudentDocumentUploadForm(forms.ModelForm):
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
    }

    class Meta:
        model = StudentDocument
        fields = ["document_type", "title", "file"]
        widgets = {
            "document_type": forms.Select(
                attrs={"class": "form-control"}
            ),
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter a document title",
                }
            ),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()

        if not title:
            raise forms.ValidationError(
                "Please enter a document title."
            )

        return title

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if not uploaded_file:
            raise forms.ValidationError(
                "Please select a document to upload."
            )

        if uploaded_file.size > self.MAX_FILE_SIZE:
            raise forms.ValidationError(
                "The file must not exceed 5 MB."
            )

        import os

        extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if extension not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "Only PDF, JPG, JPEG, and PNG files are allowed."
            )

        return uploaded_file


class StudentApplicationForm(forms.ModelForm):
    class Meta:
        model = StudentApplication
        fields = ["course", "student_statement"]
        widgets = {
            "student_statement": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": (
                        "Briefly explain your study goals "
                        "and why you selected this course."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["course"].queryset = Course.objects.all() # type: ignore
        self.fields["student_statement"].required = False


class ApplicationStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=StudentApplication.Status.choices,
        label="New application status",
    )
    note = forms.CharField(
        required=False,
        max_length=1000,
        label="Status update note",
        widget=forms.Textarea(attrs={
            "rows": 4,
            "placeholder": "Explain the status update or action required.",
        }),
    )


class CounselorNoteForm(forms.ModelForm):
    class Meta:
        model = CounselorNote
        fields = ["student", "application", "title", "note"]
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "e.g. Academic guidance session",
            }),
            "note": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": (
                    "Record academic guidance, recommendations, "
                    "or follow-up actions."
                ),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["student"].queryset = User.objects.filter( # type: ignore
            role=User.Role.STUDENT
        ).order_by("username")

        self.fields["application"].queryset = ( # type: ignore
            StudentApplication.objects.select_related(
                "student", "course"
            ).all()
        )

        self.fields["application"].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get("student")
        application = cleaned_data.get("application")

        if (
            student is not None
            and application is not None
            and application.student_id != student.id
        ):
            self.add_error(
                "application",
                "Select an application belonging to the chosen student.",
            )

        return cleaned_data
