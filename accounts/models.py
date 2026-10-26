
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for Pocket Consultancy."""

    class Role(models.TextChoices):
        STUDENT = "student", "Student"
        COUNSELOR = "counselor", "Counselor"
        DOCUMENTATION_OFFICER = (
            "documentation_officer",
            "Documentation Officer",
        )
        ADMINISTRATOR = "administrator", "Administrator"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})" # type: ignore
