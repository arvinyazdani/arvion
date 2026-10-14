"""Public reading HTML must not depend on account or message cookies."""
from urllib.parse import urlsplit
from xml.etree import ElementTree

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.cookie import CookieStorage
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.urls import resolve, reverse
from django.utils import timezone, translation

from core.public_pages import PUBLIC_CONTENT_ROUTES


class PublicShellTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from core.tests_seo_contract import WholeSitemapContractTests
        WholeSitemapContractTests.setUpTestData.__func__(cls)
        cls.customer = get_user_model().objects.create_user(
            username="public-shell-customer", email="public-shell-customer@example.invalid", password="test-only-pass")
        cls.staff = get_user_model().objects.create_user(
            username="public-shell-staff", email="public-shell-staff@example.invalid", password="test-only-pass", is_staff=True)

    def setUp(self):
        self.addCleanup(translation.deactivate_all)

    def message_cookie(self):
        storage = CookieStorage(RequestFactory().get("/fa/about/"))
        storage.add(messages.INFO, "PRIVATE-FLASH-MUST-NOT-APPEAR")
        carrier = HttpResponse()
        storage.update(carrier)
        return carrier.cookies["messages"].value

    def test_every_public_sitemap_route_is_identical_for_cookie_variants(self):
        urls = ElementTree.fromstring(Client().get("/sitemap.xml").content)
        paths = [urlsplit(loc.text).path for loc in urls.findall("{*}url/{*}loc")]
        public_paths = []
        for path in paths:
            with translation.override(path.split("/")[1]):
                if resolve(path).view_name in PUBLIC_CONTENT_ROUTES:
                    public_paths.append(path)
        paths = public_paths
        self.assertGreaterEqual(len(paths), 30)
        paths.extend(["/robots.txt", "/sitemap.xml", "/offline/", "/offline/fa/",
                      "/offline/en/", reverse("indexnow_key")])
        covered = set()
        for path in paths:
            language = path.split("/")[1]
            with translation.override(language if language in {"fa", "en"} else "fa"):
                covered.add(resolve(path).view_name)
        self.assertEqual(covered, PUBLIC_CONTENT_ROUTES)
        ordinary, staff, staff_messages = Client(), Client(), Client()
        ordinary.force_login(self.customer)
        staff.force_login(self.staff)
        staff_messages.cookies.update(staff.cookies)
        stale, flash = Client(), Client()
        stale.cookies["sessionid"] = "expired-session-that-must-not-be-repaired"
        flash.cookies["messages"] = self.message_cookie()
        staff_messages.cookies["messages"] = self.message_cookie()
        for path in paths:
            baseline = Client().get(path)
            self.assertEqual(baseline.status_code, 200)
            self.assertFalse(baseline.cookies)
            for label, client in [("customer", ordinary), ("staff", staff),
                                  ("stale session", stale), ("messages", flash),
                                  ("staff and messages", staff_messages)]:
                with self.subTest(path=path, variant=label):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.content, baseline.content)
                    self.assertFalse(response.cookies)
                    self.assertNotContains(response, "PRIVATE-FLASH-MUST-NOT-APPEAR")
                    self.assertNotContains(response, "RVION_STAFF_PUSH=true")
                    self.assertNotContains(response, "nav-management")
                    self.assertNotIn("unread_count", response.context or {})

    def test_public_read_does_not_consume_private_message(self):
        self.client.cookies["messages"] = self.message_cookie()
        public = self.client.get("/fa/about/")
        self.assertNotContains(public, "PRIVATE-FLASH-MUST-NOT-APPEAR")
        self.assertFalse(public.cookies)
        private = self.client.get("/fa/account/login/")
        self.assertContains(private, "PRIVATE-FLASH-MUST-NOT-APPEAR")
        self.assertIn("no-store", private["Cache-Control"])

    def test_staff_private_page_retains_push_context_and_csrf(self):
        self.client.force_login(self.staff)
        response = self.client.get("/fa/account/dashboard/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "RVION_STAFF_PUSH=true")
        self.assertIn("csrftoken", response.cookies)
        self.assertIn("no-store", response["Cache-Control"])

    def test_superseded_session_is_still_rejected_on_private_endpoint(self):
        first, second = Client(), Client()
        first.force_login(self.customer)
        second.force_login(self.customer)
        public = first.get("/fa/about/")
        self.assertEqual(public.status_code, 200)
        self.assertFalse(public.cookies)
        private = first.get("/fa/account/dashboard/")
        self.assertEqual(private.status_code, 302)
        self.assertIn("/account/login/", private.url)

    def test_contact_success_destination_is_private_and_never_cached(self):
        from leads.models import Lead
        from leads.views.contact import LeadCreateView
        lead = Lead.objects.create(name="Fixture", phone="09120000000", message="Fixture",
                                   privacy_accepted_at=timezone.now())
        view = LeadCreateView()
        view.lang, view.lead = "fa", lead
        destination = view.get_success_url()
        self.assertEqual(resolve(urlsplit(destination).path).view_name, "leads:thanks")
        response = self.client.get(destination)
        self.assertEqual(response.status_code, 200)
        self.assertIn("no-store", response["Cache-Control"])

    def test_public_content_preserves_existing_session_metrics_without_cookie_mutation(self):
        from traffic.models import ActiveVisitor, DailyVisitor, TrafficDay
        self.client.force_login(self.customer)
        response = self.client.get("/fa/about/")
        self.assertTrue(TrafficDay.objects.filter(date=timezone.localdate()).exists())
        self.assertTrue(DailyVisitor.objects.exists())
        self.assertTrue(ActiveVisitor.objects.get().is_authenticated)
        self.assertFalse(response.cookies)

    def test_invalid_auth_hash_is_not_repaired_or_deleted_by_public_read(self):
        from django.contrib.sessions.models import Session
        from django.contrib.auth import HASH_SESSION_KEY
        self.client.force_login(self.customer)
        session = self.client.session
        session[HASH_SESSION_KEY] = "invalid-auth-hash"
        session.save()
        key = session.session_key
        response = self.client.get("/fa/about/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.cookies)
        self.assertTrue(Session.objects.filter(session_key=key).exists())
        private = self.client.get("/fa/account/dashboard/")
        self.assertEqual(private.status_code, 302)
        self.assertIn("/account/login/", private.url)
