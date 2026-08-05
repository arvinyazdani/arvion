import re
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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
        self.assertEqual(user.verification_email_count, 1)
        self.assertIsNotNone(user.verification_sent_at)
        self.assertIn("?lang=en", mail.outbox[0].body)

    def test_registration_requires_first_and_last_name(self):
        payload = self.registration_payload()
        payload["first_name"] = ""
        payload["last_name"] = ""
        response = self.client.post(reverse("accounts:register") + "?lang=en", payload)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "first_name", "This field is required.")
        self.assertFormError(response.context["form"], "last_name", "This field is required.")
        self.assertFalse(User.objects.filter(email="arvin@example.com").exists())

    def test_user_can_complete_certificate_identity(self):
        user = User.objects.create_user(
            username="legacy@example.com", email="legacy@example.com", password="test-password-42",
            is_active=True, email_verified=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:profile_identity") + "?lang=en",
            {"first_name": "  Legacy ", "last_name": " User  Name "},
        )

        self.assertRedirects(response, reverse("accounts:dashboard") + "?lang=en")
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Legacy")
        self.assertEqual(user.last_name, "User Name")

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

    def test_unverified_user_can_request_a_fresh_link_after_cooldown(self):
        self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        user = User.objects.get(email="arvin@example.com")
        user.verification_sent_at = timezone.now() - timedelta(minutes=3)
        user.save(update_fields=["verification_sent_at"])
        mail.outbox.clear()

        response = self.client.post(
            reverse("accounts:resend_verification") + "?lang=en", {"email": "ARVIN@example.com"}
        )

        self.assertRedirects(
            response, reverse("accounts:verification_sent") + "?lang=en&resent=1"
        )
        self.assertEqual(len(mail.outbox), 1)
        user.refresh_from_db()
        self.assertEqual(user.verification_email_count, 2)
        self.assertIn("?lang=en", mail.outbox[0].body)

    def test_resend_is_throttled_and_does_not_reveal_account_existence(self):
        self.client.post(reverse("accounts:register") + "?lang=en", self.registration_payload())
        mail.outbox.clear()
        existing = self.client.post(
            reverse("accounts:resend_verification") + "?lang=en", {"email": "arvin@example.com"}
        )
        unknown = self.client.post(
            reverse("accounts:resend_verification") + "?lang=en", {"email": "unknown@example.com"}
        )

        expected = reverse("accounts:verification_sent") + "?lang=en&resent=1"
        self.assertRedirects(existing, expected)
        self.assertRedirects(unknown, expected)
        self.assertEqual(len(mail.outbox), 0)
        existing_page = self.client.get(existing.url)
        unknown_page = self.client.get(unknown.url)
        self.assertContains(existing_page, "If an eligible unverified account exists")
        self.assertContains(unknown_page, "If an eligible unverified account exists")

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
