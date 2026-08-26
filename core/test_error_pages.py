import uuid

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from accounts.models import User


@override_settings(DEBUG=False)
class BrandedErrorPageTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)

    def test_public_404_is_bilingual_and_has_recovery_actions(self):
        english = self.client.get("/en/this-page-does-not-exist/")
        self.assertEqual(english.status_code, 404)
        self.assertContains(english, "We couldn’t find that page", status_code=404)
        self.assertContains(english, "Go to home", status_code=404)
        self.assertContains(english, "noindex,nofollow,noarchive", status_code=404)

        persian = self.client.get("/fa/this-page-does-not-exist/")
        self.assertContains(persian, "این صفحه پیدا نشد", status_code=404)
        self.assertNotContains(persian, "We couldn’t find that page", status_code=404)

    def test_staff_permission_denial_stays_inside_management_workspace(self):
        staff = User.objects.create_user(
            username="limited-staff@example.com",
            email="limited-staff@example.com",
            password="safe-test-password",
            is_staff=True,
            is_active=True,
        )
        self.client.force_login(staff)
        response = self.client.get("/en/management/contracts/settings/")
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "This action isn’t included in your current role", status_code=403)
        self.assertContains(response, reverse("management_portal:dashboard"), status_code=403)
        self.assertNotContains(response, "403 Forbidden", status_code=403)

    def test_html_405_has_branded_recovery_page_and_preserves_allow_header(self):
        user = User.objects.create_user(
            username="method@example.com", email="method@example.com",
            password="safe-test-password", is_active=True,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("assessments:manual_payment_submit", args=[uuid.uuid4()]),
            HTTP_ACCEPT="text/html",
        )

        self.assertEqual(response.status_code, 405)
        self.assertContains(response, "این عملیات از این مسیر قابل انجام نیست", status_code=405)
        self.assertEqual(response.headers["Allow"], "POST, OPTIONS")
