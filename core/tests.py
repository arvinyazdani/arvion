from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from .i18n_numbers import normalize_digits, persian_digits
from .jalali import format_jalali, gregorian_to_jalali, jalali_to_gregorian
from .models import CompanyProfile
from projects.models import Project


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
        self.assertContains(response, "core/icons/icon-192.png")
        self.assertContains(response, 'data-install-guide', html=False)
        self.assertContains(response, 'data-install-panel="ios"', html=False)
        self.assertContains(response, 'data-install-panel="android"', html=False)
        self.assertContains(response, 'data-install-panel="desktop"', html=False)
        self.assertContains(response, 'data-app-welcome', html=False)
        self.assertRedirects(self.client.get("/favicon.ico"), "/static/core/favicon.svg", status_code=301, fetch_redirect_response=False)

    def test_language_prefixed_urls_and_root_redirect(self):
        with translation.override("fa"):
            self.assertEqual(reverse("home"), "/fa/")
        with translation.override("en"):
            self.assertEqual(reverse("services:list"), "/en/services/")
        response = self.client.get("/")
        self.assertRedirects(response, "/fa/", status_code=301, fetch_redirect_response=False)

    def test_seo_metadata_uses_production_canonical_and_alternates(self):
        response = self.client.get("/en/services/")
        self.assertContains(response, '<link rel="canonical" href="https://rvionai.com/en/services/">', html=True)
        self.assertContains(response, 'hreflang="fa" href="https://rvionai.com/fa/services/"', html=False)
        self.assertContains(response, 'hreflang="x-default"', html=False)
        self.assertContains(response, '"@type":"Organization"', html=False)
        self.assertContains(response, 'property="og:image"', html=False)
        self.assertContains(response, "rvion-whatsapp-share-v2.png")
        self.assertContains(response, 'property="og:image:url"', html=False)
        self.assertContains(response, "https://wa.me/?text=")
        self.assertNotContains(response, "?lang=")

    def test_public_pages_offer_whatsapp_share_but_private_pages_do_not(self):
        public_response = self.client.get("/fa/")
        self.assertContains(public_response, "اشتراک در واتساپ")
        self.assertContains(public_response, "rvionai.com/fa/")
        private_response = self.client.get("/fa/account/login/")
        self.assertNotContains(private_response, 'class="whatsapp-share"', html=False)

    def test_robots_and_bilingual_sitemap_are_public(self):
        robots = self.client.get(reverse("robots"))
        self.assertContains(robots, "Sitemap: https://rvionai.com/sitemap.xml")
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

    def test_public_responses_apply_browser_security_boundaries(self):
        response = self.client.get("/fa/")
        policy = response["Content-Security-Policy"]
        self.assertIn("object-src 'none'", policy)
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertIn("form-action 'self'", policy)
        self.assertEqual(response["X-Permitted-Cross-Domain-Policies"], "none")
        self.assertIn("camera=()", response["Permissions-Policy"])

    def test_saved_theme_is_bootstrapped_before_stylesheets(self):
        response = self.client.get("/fa/")
        html = response.content.decode()
        bootstrap = html.index("localStorage.getItem('rvion-theme')")
        tokens = html.index("core/css/tokens.css")
        self.assertLess(bootstrap, tokens)
        self.assertContains(response, 'data-theme-toggle', html=False)

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
        self.assertContains(response, "آرویون | طراحی و توسعه محصول دیجیتال")
        self.assertContains(response, "شناسه ملی 14015444540")
        self.assertNotContains(response, ">ARVION<", html=False)
        self.assertNotContains(response, ">رویون<", html=False)

    def test_delivery_card_is_fully_localized_and_public_email_is_hidden(self):
        fa_response = self.client.get("/fa/")
        self.assertContains(fa_response, "از نیاز کسب‌وکار")
        self.assertContains(fa_response, "شفاف")
        self.assertNotContains(fa_response, "hello@rvin-tech.com")

        en_response = self.client.get("/en/")
        self.assertContains(en_response, "From business need")
        self.assertContains(en_response, "Defined")
        self.assertContains(en_response, "Supported")
        delivery_html = en_response.content.decode().split('class="hero-panel"', 1)[1].split("</section>", 1)[0]
        self.assertNotRegex(delivery_html, r"[۰-۹]")
        self.assertNotIn("hello@rvin-tech.com", en_response.content.decode())

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
        self.assertContains(response, "فرآیند پیچیده")
        self.assertContains(response, "راهکارهای آرویون")
        self.assertContains(response, "چه کاری انجام می‌دهیم")
        self.assertContains(response, "هویت حقوقی و اطلاعات قابل استعلام")
        self.assertNotContains(response, "۲۴ پروژه")

    def test_home_only_displays_real_published_project_count(self):
        Project.objects.create(title_fa="نمونه واقعی", title_en="Real case", slug="real-case", is_active=True)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "پروژه منتشرشده و قابل مشاهده")
        self.assertEqual(response.context["published_project_count"], Project.objects.filter(is_active=True).count())

    def test_crm_product_overview_is_read_only_bilingual_and_internally_linked(self):
        persian = self.client.get("/fa/crm/")
        english = self.client.get("/en/crm/")

        self.assertContains(persian, "همه ارتباطات مشتری؛ از اولین تماس تا فروش و پشتیبانی")
        self.assertContains(persian, "مدیریت مشتریان")
        self.assertContains(persian, "PostgreSQL تحت مالکیت مشتری")
        self.assertContains(english, "Every customer interaction")
        self.assertContains(english, "Customer management")
        self.assertNotContains(persian, "<form", html=False)
        self.assertNotRegex(persian.content.decode(), r'href=["\']https?://(?!testserver|rvionai\.com)')
        self.assertContains(persian, 'href="/fa/crm-order/"', html=False)

        home = self.client.get("/fa/")
        self.assertContains(home, "معرفی کامل راهکار")
        self.assertContains(home, 'href="/fa/crm/"', html=False)

    def test_service_worker_is_served_from_root_for_full_app_scope(self):
        response = self.client.get(reverse("service_worker"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("application/javascript", response["Content-Type"])
        self.assertContains(response, 'const CACHE = "rvion-shell-v3"')

    def test_persian_and_arabic_digits_are_normalized(self):
        self.assertEqual(normalize_digits("۱۲٣٫۴۵"), "123.45")

    def test_jalali_payment_date_conversion_is_reversible(self):
        from datetime import date
        gregorian = date(2026, 8, 10)
        self.assertEqual(gregorian_to_jalali(gregorian), (1405, 5, 19))
        self.assertEqual(format_jalali(gregorian, persian_digits=True, month_name=True), "۱۹ مرداد ۱۴۰۵")
        self.assertEqual(jalali_to_gregorian(1405, 5, 19), gregorian)

    def test_ascii_digits_are_rendered_as_persian(self):
        self.assertEqual(persian_digits("2026 / 50"), "۲۰۲۶ / ۵۰")

    def test_language_is_selected_by_url_prefix(self):
        response = self.client.get("/en/about/")
        self.assertEqual(response.context["lang"], "en")
        self.assertContains(response, "Technology for")

    def test_invalid_language_falls_back_to_persian(self):
        response = self.client.get(reverse("home"), {"lang": "xx"})
        self.assertEqual(response.context["lang"], "fa")
