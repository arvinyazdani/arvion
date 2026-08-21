from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User


@override_settings(DEBUG=False)
class BrandedErrorPageTests(TestCase):
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
