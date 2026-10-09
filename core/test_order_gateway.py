from urllib.parse import parse_qs, urlsplit
from django.test import TestCase
from django.utils.html import escape
from projects.models import DemoTemplate, DemoSelection
from core.order_paths import TOPICS


class OrderGatewayTests(TestCase):
    def setUp(self):
        self.demo = DemoTemplate.objects.create(slug="gateway-store", category="ecommerce", title_fa="نمونه فروشگاه", title_en="Sample store", tagline_fa="محصول و پرداخت", tagline_en="Products and payments", fictional_brand_fa="نمونه", fictional_brand_en="Sample", style_key="minimal")

    def test_each_topic_has_bilingual_selection_page(self):
        for lang in ("fa", "en"):
            for topic in TOPICS:
                response = self.client.get(f"/{lang}/start/", {"type": topic.key})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, escape(getattr(topic, "title_" + lang)))
                if lang == "en":
                    self.assertNotContains(response, "چه چیزی می‌خواهید بسازید؟")

    def test_final_destinations_and_specialist_language_notice(self):
        for topic in TOPICS:
            expected = "/fa/clinic-order/" if topic.key == "clinic" else "/fa/crm-order/" if topic.key == "crm" else "/en/contact/"
            response = self.client.get("/en/start/", {"type": topic.key, "go": "form"})
            self.assertEqual(response.status_code, 302)
            self.assertEqual(urlsplit(response.url).path, expected)
        self.assertContains(self.client.get("/en/start/?type=crm"), "The specialist form is currently in Persian.")

    def test_preview_reuses_existing_template_without_new_storage(self):
        response = self.client.get("/fa/start/", {"type": "ecommerce", "sample": self.demo.slug, "go": "preview", "addons": "support", "name": "PRIVATE"})
        self.assertEqual(urlsplit(response.url).path, "/fa/projects/demos/gateway-store/")
        self.assertNotIn("PRIVATE", response.url)
        self.assertIn("addons=support", response.url)
        self.assertEqual(DemoSelection.objects.count(), 0)
        # LanguageViewMixin already stores lang; gateway adds no selection state.
        self.assertEqual(dict(self.client.session), {"lang": "fa"})

    def test_foreign_category_unknown_and_external_sample_are_ignored(self):
        for sample in (self.demo.slug, "https://example.com/"):
            response = self.client.get("/fa/start/", {"type": "clinic", "sample": sample, "go": "preview"})
            self.assertEqual(response.status_code, 200)
        response = self.client.get("/fa/start/", {"type": "unknown"})
        self.assertContains(response, 'class="project-start-card', count=9)

    def test_consultation_uses_short_general_form(self):
        response = self.client.get("/fa/start/", {"type": "crm", "consult": "1"})
        self.assertEqual(urlsplit(response.url).path, "/fa/contact/")

    def test_existing_urls_preserved_and_specialist_en_redirect_is_explicit(self):
        for path in ("/fa/contact/", "/fa/crm-order/", "/fa/clinic-order/"):
            self.assertEqual(self.client.get(path).status_code, 200)
        for path in ("crm-order", "clinic-order"):
            self.assertRedirects(self.client.get(f"/en/{path}/"), f"/fa/{path}/")
