from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from blog.models import Post
from core.indexnow import INDEXNOW_KEY, submit_urls
from core.sitemaps import StaticSitemap
from projects.models import DemoTemplate


class CostCalculatorPageTests(TestCase):
    def test_bilingual_pages_are_indexable_cookie_free_and_have_web_application_schema(self):
        for language in ("fa", "en"):
            with self.subTest(language=language):
                response = self.client.get(f"/{language}/tools/cost-calculator/")
                self.assertEqual(response.status_code, 200)
                self.assertFalse(response.cookies)
                html = response.content.decode()
                self.assertIn('name="robots" content="index,follow', html)
                self.assertIn('rel="canonical"', html)
                self.assertIn('hreflang="fa"', html)
                self.assertIn('hreflang="en"', html)
                self.assertIn("WebApplication", html)
                self.assertIn("BreadcrumbList", html)
                self.assertIn('id="cost-calculator-data"', html)
                self.assertIn("<noscript>", html)
                self.assertIn("aria-live=\"polite\"", html)

    def test_calculator_is_in_bilingual_sitemap_and_footer_and_home(self):
        items = StaticSitemap().items()
        self.assertIn(("fa", "cost_calculator"), items)
        self.assertIn(("en", "cost_calculator"), items)
        for lang in ("fa", "en"):
            for path in (f"/{lang}/", f"/{lang}/services/", f"/{lang}/tools/cost-calculator/"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(f"/{lang}/tools/cost-calculator/", response.content.decode())
                if path.endswith("/"):
                    html = response.content.decode()
                    self.assertIn(f"/{lang}/projects/demos/raya-personal-finance/", html)
                    self.assertIn(f"/{lang}/projects/demos/ahanino-b2b-marketplace/", html)

    def test_contextual_links_from_service_crm_gallery_and_cost_article(self):
        post = Post.objects.create(
            title_fa="هزینه نرم‌افزار", title_en="Software cost", slug_fa="custom-software-cost-us-2026-crm-accounting-b2b",
            slug_en="custom-software-cost-us-2026-crm-accounting-b2b", body_fa="متن", body_en="Body", is_published=True,
            published_at=timezone.now(),
        )
        DemoTemplate.objects.create(
            slug="cost-link-test-demo", category="corporate", title_fa="نمونه", title_en="Demo",
            tagline_fa="توضیح", tagline_en="Tagline", fictional_brand_fa="فرضی", fictional_brand_en="Fictional",
            style_key="modern", is_active=True,
        )
        for lang in ("fa", "en"):
            for path in (f"/{lang}/services/", f"/{lang}/crm/", f"/{lang}/projects/demos/", f"/{lang}/blog/custom-software-cost-us-2026-crm-accounting-b2b/"):
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, f"/{lang}/tools/cost-calculator/")
                    self.assertContains(response, f"/{lang}/projects/demos/raya-personal-finance/")
                    self.assertContains(response, f"/{lang}/projects/demos/ahanino-b2b-marketplace/")

    def test_calculator_links_to_cost_guides_and_raya_demo_links_to_live_product(self):
        response = self.client.get("/fa/tools/cost-calculator/")
        self.assertContains(response, "/en/blog/custom-software-cost-us-2026-crm-accounting-b2b/")
        self.assertContains(response, "/en/blog/hire-django-freelancer-us-rates-2026/")
        self.assertContains(response, "/fa/blog/custom-software-cost-us-2026-crm-accounting-b2b/")
        self.assertTrue(DemoTemplate.objects.filter(slug="raya-personal-finance", is_active=True).exists())
        gallery = self.client.get("/fa/projects/demos/")
        self.assertEqual(gallery.status_code, 200)
        self.assertContains(gallery, "https://raya.rvionai.com/")

    def test_demo_preview_remains_csrf_protected_and_contact_has_csrf_cookie(self):
        from django.conf import settings
        demo = DemoTemplate.objects.create(
            slug="calculator-csrf-demo", category="corporate", title_fa="نمونه", title_en="Demo",
            tagline_fa="توضیح", tagline_en="Tagline", fictional_brand_fa="فرضی", fictional_brand_en="Fictional",
            style_key="modern", is_active=True,
        )
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        response = client.get(f"/fa/projects/demos/{demo.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(settings.CSRF_COOKIE_NAME, response.cookies)
        self.assertEqual(client.post(f"/fa/projects/demos/{demo.slug}/configure/", {}).status_code, 403)

    def test_calculator_prefill_uses_allowlisted_choices_and_rejects_invalid_product(self):
        from core.order_summary import calculator_initial
        class Request:
            GET = {"estimate": "1", "product": "crm", "roles": "4", "integrations": "2",
                   "erp": "1", "mobile": "1", "legal": "0", "team": "company", "maintenance": "15",
                   "message": "ignore"}
        result = calculator_initial(Request(), {}, "en")
        self.assertIn("Custom CRM", result["message"])
        self.assertIn("User roles: 4", result["message"])
        self.assertNotIn("ignore", result["message"])
        Request.GET = {"estimate": "1", "product": "<script>", "team": "company"}
        self.assertEqual(calculator_initial(Request(), {}, "en"), {})

    def test_contact_form_prefills_estimate_without_creating_or_persisting_a_lead(self):
        from leads.models import Lead
        response = self.client.get(
            "/en/contact/?estimate=1&product=crm&roles=4&integrations=2&erp=1&mobile=1&legal=0&team=company&maintenance=15"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cost calculator selections (draft):")
        self.assertContains(response, "Custom CRM")
        self.assertContains(response, "User roles: 4")
        self.assertEqual(Lead.objects.count(), 0)


class IndexNowTests(TestCase):
    @override_settings(INDEXNOW_ENABLED=True, SITE_URL="https://rvionai.com")
    @patch("core.indexnow.urlopen")
    def test_submit_only_same_site_urls_and_posts_indexnow_payload(self, mocked_open):
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): return False
        mocked_open.return_value = Response()
        result = submit_urls(["https://rvionai.com/en/tools/cost-calculator/", "https://evil.example/x"])
        self.assertEqual(result["status"], "accepted")
        request = mocked_open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.indexnow.org/indexnow")
        self.assertIn(INDEXNOW_KEY.encode(), request.data)
        self.assertIn(b"rvionai.com/en/tools/cost-calculator/", request.data)
        self.assertNotIn(b"evil.example", request.data)

    @override_settings(INDEXNOW_ENABLED=True, SITE_URL="https://rvionai.com")
    @patch("core.indexnow_signals.submit_urls")
    def test_publishing_or_editing_post_notifies_bilingual_urls_after_commit(self, mocked_submit):
        with self.captureOnCommitCallbacks(execute=True):
            post = Post.objects.create(
                title_fa="عنوان", title_en="Title", summary_fa="خلاصه", summary_en="Summary",
                slug_fa="indexnow-fa", slug_en="indexnow-en", body_fa="متن", body_en="Body",
                is_published=False,
            )
        mocked_submit.assert_not_called()
        post.is_published = True
        post.published_at = timezone.now()
        with self.captureOnCommitCallbacks(execute=True):
            post.save()
        mocked_submit.assert_called_once()
        self.assertEqual(set(mocked_submit.call_args.args[0]), {
            "https://rvionai.com/fa/blog/indexnow-fa/", "https://rvionai.com/en/blog/indexnow-en/"})

    def test_public_key_file_is_exact_text(self):
        response = self.client.get(f"/{INDEXNOW_KEY}.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode().strip(), INDEXNOW_KEY)

    @override_settings(INDEXNOW_ENABLED=True, SITE_URL="https://rvionai.com")
    @patch("core.indexnow_signals.submit_urls")
    def test_activating_demo_notifies_both_localized_public_urls(self, mocked_submit):
        with self.captureOnCommitCallbacks(execute=True):
            DemoTemplate.objects.create(
                slug="indexnow-demo", category="corporate", title_fa="نمونه", title_en="Sample",
                tagline_fa="توضیح", tagline_en="Description", fictional_brand_fa="فرضی",
                fictional_brand_en="Fictional", style_key="modern", is_active=True,
            )
        mocked_submit.assert_called_once()
        self.assertEqual(set(mocked_submit.call_args.args[0]), {
            "https://rvionai.com/fa/projects/demos/indexnow-demo/",
            "https://rvionai.com/en/projects/demos/indexnow-demo/",
        })
