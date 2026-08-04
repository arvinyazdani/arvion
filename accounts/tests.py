import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse


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
