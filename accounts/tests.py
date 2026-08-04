import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

from assessments.models import Exam, ExamEntitlement, Order


User = get_user_model()


class AccountFlowTests(TestCase):
    def registration_payload(self):
        return {
            "first_name": "Arvin",
            "last_name": "Yazdani",
            "email": "ARVIN@example.com",
            "password1": "A-secure-test-password-42",
            "password2": "A-secure-test-password-42",
        }

    def test_registration_creates_inactive_user_and_sends_verification(self):
        response = self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        self.assertRedirects(response, reverse("accounts:verification_sent") + "?lang=en")
        user = User.objects.get(email="arvin@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertEqual(user.username, user.email)
        self.assertEqual(len(mail.outbox), 1)

    def test_verification_activates_and_logs_user_in(self):
        self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        verify_url = re.search(r"http://testserver([^\s]+)", mail.outbox[0].body).group(1)
        response = self.client.get(verify_url)
        user = User.objects.get(email="arvin@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)
        self.assertRedirects(response, reverse("accounts:dashboard") + "?lang=en")

    def test_unverified_user_cannot_log_in(self):
        self.client.post(reverse("accounts:register"), self.registration_payload())
        response = self.client.post(reverse("accounts:login"), {"username": "arvin@example.com", "password": "A-secure-test-password-42"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}")

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(username="arvin@example.com", email="arvin@example.com", password="test")
        response = self.client.post(reverse("accounts:register"), self.registration_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="arvin@example.com").count(), 1)

    def test_dashboard_groups_multiple_attempts_for_same_exam(self):
        user = User.objects.create_user(
            username="group@example.com", email="group@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        exam = Exam.objects.create(
            slug="grouped-exam", title_fa="آزمون گروه‌بندی", title_en="Grouped exam",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )
        for _ in range(2):
            order = Order.objects.create(user=user, exam=exam, amount_irr=500_000, status="paid")
            ExamEntitlement.objects.create(user=user, exam=exam, order=order, attempts_remaining=1)
        self.client.force_login(user)
        response = self.client.get(reverse("accounts:dashboard"))
        self.assertEqual(response.content.decode().count("آزمون گروه‌بندی"), 1)
        self.assertEqual(response.context["assessment_groups"][0]["ready"], 2)
