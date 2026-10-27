
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class StudentRegistrationTests(TestCase):
    def test_registration_page_loads(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_student_registration_requires_approval(self):
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

        self.assertRedirects(response, reverse("accounts:login"))

        user = User.objects.get(username="student01")
        self.assertEqual(user.role, User.Role.STUDENT) # type: ignore
        self.assertEqual(
            user.approval_status, # type: ignore
            User.ApprovalStatus.PENDING, # type: ignore
        )
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password("StrongTestPass!827"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_public_registration_cannot_assign_privileged_role(self):
        self.client.post(
            reverse("accounts:register"),
            {
                "username": "attemptedadmin",
                "first_name": "Attempt",
                "last_name": "Admin",
                "email": "attempt@example.com",
                "password1": "StrongTestPass!827",
                "password2": "StrongTestPass!827",
                "role": User.Role.ADMINISTRATOR, # type: ignore
                "approval_status": User.ApprovalStatus.APPROVED, # type: ignore
                "is_active": "true",
            },
        )

        user = User.objects.get(username="attemptedadmin")
        self.assertEqual(user.role, User.Role.STUDENT) # type: ignore
        self.assertEqual(
            user.approval_status, # type: ignore
            User.ApprovalStatus.PENDING, # type: ignore
        )
        self.assertFalse(user.is_active)

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username="existing",
            email="student@example.com",
            password="ExistingPass!827",
            approval_status=User.ApprovalStatus.APPROVED, # type: ignore
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


class AccountApprovalLoginTests(TestCase):
    def setUp(self):
        self.login_url = reverse("accounts:login")

    def create_user(self, username, status, is_active):
        return User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="StrongTestPass!827",
            approval_status=status,
            is_active=is_active,
        )

    def test_pending_account_cannot_login(self):
        self.create_user(
            "pendinguser",
            User.ApprovalStatus.PENDING, # type: ignore
            False,
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "pendinguser",
                "password": "StrongTestPass!827",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_rejected_account_cannot_login(self):
        self.create_user(
            "rejecteduser",
            User.ApprovalStatus.REJECTED, # type: ignore
            False,
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "rejecteduser",
                "password": "StrongTestPass!827",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_approved_active_account_can_login(self):
        self.create_user(
            "approveduser",
            User.ApprovalStatus.APPROVED, # type: ignore
            True,
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "approveduser",
                "password": "StrongTestPass!827",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_pending_status_blocks_login_even_if_active(self):
        # Approval status must be enforced independently of is_active.
        self.create_user(
            "inconsistentuser",
            User.ApprovalStatus.PENDING, # type: ignore
            True,
        )

        response = self.client.post(
            self.login_url,
            {
                "username": "inconsistentuser",
                "password": "StrongTestPass!827",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
