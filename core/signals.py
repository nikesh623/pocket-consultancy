
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from .models import StudentProfile


@receiver(post_save, sender=User)
def create_student_profile(sender, instance, created, **kwargs):
    if created and instance.role == User.Role.STUDENT:
        StudentProfile.objects.get_or_create(user=instance)
