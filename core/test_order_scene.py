from urllib.parse import parse_qs, urlsplit
from django.test import TestCase
from projects.models import DemoTemplate, DemoSelection


class OrderSceneHandoffTests(TestCase):
    def setUp(self):
        self.demo = DemoTemplate.objects.create(slug="scene-store", category="ecommerce", title_fa="نمونه", title_en="Sample", fictional_brand_fa="نمونه", fictional_brand_en="Sample", style_key="minimal")
        self.payload = {"wizard_submission": "1", "type": "ecommerce", "palette": "rose", "look": "industrial", "features": ["payment", "catalog", "foreign"], "submission_token": "scene-test-token", "brand_preview": "PRIVATE", "brand": "PRIVATE", "redirect": "https://foreign/"}

    def test_features_use_existing_session_bound_handoff_without_brand(self):
        response = self.client.post("/fa/start/", self.payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).path, "/fa/contact/")
        row = DemoSelection.objects.get()
        self.assertEqual(row.selections["features"], ["catalog", "payment"])
        self.assertEqual(row.selections["brand"], "نمونه")
        self.assertNotIn("PRIVATE", str(row.selections) + response.url)
        self.assertNotIn("foreign", str(row.selections) + response.url)
        self.assertEqual(parse_qs(urlsplit(response.url).query)["palette"], ["rose"])
        self.assertEqual(row.session_key, self.client.session.session_key)
        page = self.client.get(response.url)
        self.assertContains(page, "امکانات انتخاب‌شدهٔ شما")
        self.assertContains(page, "مرجع فنی")
        self.assertNotContains(page, 'Design personality')
        self.assertTrue(page.context["order_scene_receipt"])

    def test_english_functional_receipt_never_implies_neutral_carrier_look_is_selected(self):
        response = self.client.post("/en/start/", self.payload)
        page = self.client.get(response.url)
        self.assertContains(page, "Your selected capabilities")
        self.assertContains(page, "not your final visual design")
        self.assertNotContains(page, "Design personality")
        self.assertNotContains(page, 'Colour</dt>')

    def test_retry_is_idempotent_and_different_payload_never_overwrites(self):
        first = self.client.post("/fa/start/", self.payload)
        self.assertEqual(self.client.post("/fa/start/", self.payload).url, first.url)
        changed = self.client.post("/fa/start/", {**self.payload, "features": ["blog"]})
        self.assertIn("wizard_error=retry", changed.url)
        self.assertEqual(DemoSelection.objects.count(), 1)
        self.assertEqual(DemoSelection.objects.get().selections["features"], ["catalog", "payment"])

    def test_no_feature_and_crm_routes_require_no_selection_record(self):
        response = self.client.post("/en/start/", {**self.payload, "features": []})
        self.assertEqual(urlsplit(response.url).path, "/en/contact/")
        response = self.client.post("/en/start/", {**self.payload, "type": "crm", "modules": "sales,foreign", "extensions": "ai"})
        self.assertEqual(urlsplit(response.url).path, "/fa/crm-order/")
        self.assertIn("modules=sales", response.url)
        self.assertEqual(DemoSelection.objects.count(), 0)

    def test_missing_sample_and_missing_token_have_visible_recovery(self):
        DemoTemplate.objects.filter(category="restaurant").update(is_active=False)
        for payload, error in (({**self.payload, "type": "restaurant"}, "unavailable"), ({**self.payload, "submission_token": ""}, "retry")):
            response = self.client.post("/fa/start/", payload)
            self.assertIn("wizard_error=" + error, response.url)
            self.assertContains(self.client.get(response.url), 'data-os-error')
        self.assertEqual(DemoSelection.objects.count(), 0)

    def test_page_keeps_fallback_and_loads_only_scoped_assets(self):
        response = self.client.get("/en/start/")
        self.assertContains(response, 'order-scene.js')
        self.assertContains(response, 'order-wizard-data')
        self.assertContains(response, 'class="project-start-card', count=10)
        self.assertNotContains(self.client.get("/en/"), 'order-scene.js')
