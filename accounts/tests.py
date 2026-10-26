
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class StudentRegistrationTests(TestCase):
    def test_registration_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_student_can_register(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "student01",
                "first_name": "Test",
                "last_name": "Student",
                "email": "student@example.com",
                "password1": "StrongTestPass!827",
                "password2": "StrongTestPass!827",
            },
        )

        self.assertTrue(
            User.objects.filter(username="student01").exists()
        )

        user = User.objects.get(username="student01")
        self.assertEqual(user.role, User.Role.STUDENT) # type: ignore
        self.assertTrue(user.check_password("StrongTestPass!827"))

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing",
            email="student@example.com",
            password="ExistingPass!827",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "anotherstudent",
                "first_name": "Another",
                "last_name": "Student",
                "email": "STUDENT@example.com",
                "password1": "StrongTestPass!827",
                "password2": "StrongTestPass!827",
            },
        )

        self.assertFalse(
            User.objects.filter(username="anotherstudent").exists()
        )
