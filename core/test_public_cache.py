"""Anonymous SEO caching must never weaken forms or user isolation."""
from django.conf import settings
from django.contrib.sessions.models import Session
from django.test import Client, TestCase
from django.utils import translation


class PublicCookiePolicyTests(TestCase):
    def setUp(self):
        self.addCleanup(translation.deactivate_all)

    def test_read_only_public_pages_are_cookieless_and_vary_by_cookie(self):
        for language in ("fa", "en"):
            for path in ("", "about/", "company/", "privacy/", "service-terms/",
                         "refund-policy/", "services/", "projects/demos/", "assessments/", "tools/cost-calculator/"):
                with self.subTest(language=language, path=path):
                    response = Client().get(f"/{language}/{path}")
                    self.assertEqual(response.status_code, 200)
                    self.assertFalse(response.cookies)
                    self.assertIn("public", response["Cache-Control"])
                    self.assertIn("s-maxage=60", response["Cache-Control"])
                    self.assertIn("Cookie", response["Vary"])
        self.assertFalse(Session.objects.exists())

    def test_forms_keep_csrf_cookie_and_are_never_shared_cacheable(self):
        for path in ("/fa/contact/", "/en/contact/", "/fa/account/login/", "/fa/start/"):
            with self.subTest(path=path):
                client = Client(enforce_csrf_checks=True)
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(settings.CSRF_COOKIE_NAME, response.cookies)
                self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
                self.assertIn("private", response["Cache-Control"])
                self.assertIn("no-store", response["Cache-Control"])
                rejected = client.post(path, {})
                self.assertEqual(rejected.status_code, 403)
                token = client.cookies[settings.CSRF_COOKIE_NAME].value
                accepted = client.post(path, {}, HTTP_X_CSRFTOKEN=token)
                self.assertNotEqual(accepted.status_code, 403)

    def test_existing_cookie_and_query_variants_are_private(self):
        client = Client()
        client.cookies[settings.SESSION_COOKIE_NAME] = "nonexistent-session"
        response = client.get("/fa/about/")
        self.assertIn("private", response["Cache-Control"])
        self.assertNotIn("s-maxage", response["Cache-Control"])
        self.assertIn("private", Client().get("/fa/about/?lang=en")["Cache-Control"])

    def test_authenticated_public_page_cannot_enter_shared_cache(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username="cache-test", email="cache-test@example.invalid", password="test-only-pass")
        self.client.force_login(user)
        response = self.client.get("/fa/")
        self.assertIn("private", response["Cache-Control"])
        self.assertIn("no-store", response["Cache-Control"])
        self.assertNotIn("s-maxage", response["Cache-Control"])
