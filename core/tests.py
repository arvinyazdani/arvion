from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from .i18n_numbers import normalize_digits, persian_digits
from .models import CompanyProfile


class CorePagesTests(TestCase):
    def test_mobile_shell_has_accessible_menu_and_quick_navigation(self):
        response = self.client.get("/fa/")
        self.assertContains(response, 'aria-controls="site-nav"', html=False)
        self.assertContains(response, 'aria-expanded="false"', html=False)
        self.assertContains(response, 'data-close-label="بستن منو"', html=False)
        self.assertContains(response, 'class="mobile-tabbar"', html=False)
        self.assertContains(response, 'aria-label="دسترسی سریع"', html=False)
        self.assertContains(response, 'aria-current="page"', html=False)
        self.assertContains(response, "core/js/site-shell.js")
        self.assertContains(response, "core/manifest.webmanifest")
        self.assertContains(response, "core/favicon.svg")

    def test_language_prefixed_urls_and_root_redirect(self):
        with translation.override("fa"):
            self.assertEqual(reverse("home"), "/fa/")
        with translation.override("en"):
            self.assertEqual(reverse("services:list"), "/en/services/")
        response = self.client.get("/")
        self.assertRedirects(response, "/fa/", status_code=301, fetch_redirect_response=False)

    def test_seo_metadata_uses_production_canonical_and_alternates(self):
        response = self.client.get("/en/services/")
        self.assertContains(response, '<link rel="canonical" href="https://rvin-tech.com/en/services/">', html=True)
        self.assertContains(response, 'hreflang="fa" href="https://rvin-tech.com/fa/services/"', html=False)
        self.assertContains(response, 'hreflang="x-default"', html=False)
        self.assertContains(response, '"@type":"Organization"', html=False)
        self.assertNotContains(response, "?lang=")

    def test_robots_and_bilingual_sitemap_are_public(self):
        robots = self.client.get(reverse("robots"))
        self.assertContains(robots, "Sitemap: https://rvin-tech.com/sitemap.xml")
        self.assertContains(robots, "Disallow: /admin/")
        sitemap = self.client.get(reverse("sitemap"))
        self.assertContains(sitemap, "https://testserver/fa/services/")
        self.assertContains(sitemap, "https://testserver/en/services/")

    def test_application_shell_exposes_accessible_landmarks_and_controls(self):
        response = self.client.get(reverse("home") + "?lang=fa")
        self.assertContains(response, 'class="skip-link"')
        self.assertContains(response, '<main id="main" tabindex="-1">')
        self.assertContains(response, 'aria-label="پیمایش اصلی"')
        self.assertContains(response, 'aria-controls="site-nav"')
        self.assertContains(response, 'aria-expanded="false"')

    def test_company_identity_is_seeded_once(self):
        company = CompanyProfile.objects.get()
        self.assertEqual(company.legal_name_fa, "آروین توسعه تجارت هوشمند")
        self.assertEqual(company.registration_number, "675342")
        self.assertEqual(company.national_id, "14015444540")
        self.assertEqual(company.postal_code, "1683445995")
        self.assertEqual(company.brand_name, "Rvion")

    def test_company_and_legal_pages_are_public_and_bilingual(self):
        cases = (
            ("about", "آروین یزدانی", "Arvin Yazdani"),
            ("company_info", "675342", "Registration number"),
            ("privacy", "حریم خصوصی", "Privacy policy"),
            ("service_terms", "۵۰٪", "50% on commencement"),
            ("refund_policy", "دو ساعت", "within two hours"),
        )
        for name, fa_text, en_text in cases:
            with self.subTest(page=name, lang="fa"):
                self.assertContains(self.client.get(reverse(name) + "?lang=fa"), fa_text)
            with self.subTest(page=name, lang="en"):
                self.assertContains(self.client.get(reverse(name) + "?lang=en"), en_text)

    def test_global_brand_and_legal_footer_use_rvion(self):
        response = self.client.get(reverse("home") + "?lang=fa")
        self.assertContains(response, ">RVION<", html=False)
        self.assertContains(response, "شناسه ملی 14015444540")
        self.assertNotContains(response, ">ARVION<", html=False)

    def test_company_page_does_not_claim_an_unissued_trust_seal(self):
        response = self.client.get(reverse("company_info") + "?lang=fa")
        self.assertContains(response, "فرآیند دریافت اینماد در حال تکمیل است")
        self.assertNotContains(response, "logo.aspx")

    def test_health_check_confirms_database_connection(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_fails_closed_without_leaking_error(self):
        with patch.object(connection, "cursor", side_effect=RuntimeError("database secret detail")):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotContains(response, "secret detail", status_code=503)

    def test_home_defaults_to_persian(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["lang"], "fa")
        self.assertContains(response, "ایده‌ات را")

    def test_persian_and_arabic_digits_are_normalized(self):
        self.assertEqual(normalize_digits("۱۲٣٫۴۵"), "123.45")

    def test_ascii_digits_are_rendered_as_persian(self):
        self.assertEqual(persian_digits("2026 / 50"), "۲۰۲۶ / ۵۰")

    def test_language_is_selected_by_url_prefix(self):
        response = self.client.get("/en/about/")
        self.assertEqual(response.context["lang"], "en")
        self.assertContains(response, "Technology for")

    def test_invalid_language_falls_back_to_persian(self):
        response = self.client.get(reverse("home"), {"lang": "xx"})
        self.assertEqual(response.context["lang"], "fa")
