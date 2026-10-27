
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user for Pocket Consultancy."""

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        COUNSELOR = "counselor", "Counselor"
        DOCUMENTATION_OFFICER = (
            "documentation_officer",
            "Documentation Officer",
        )
        ADMINISTRATOR = "administrator", "Administrator"

    class ApprovalStatus(models.TextChoices):
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    approval_status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.choices,
        default=ApprovalStatus.PENDING,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})" # type: ignore
