from urllib.parse import urlsplit

from django.core.cache import cache
from django.test import TestCase
from django.utils import translation

from projects.models import DemoSelection, DemoTemplate


class UnifiedOrderHandoffTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.demo = DemoTemplate.objects.create(slug="order-clinic", category="clinic", title_fa="کلینیک نمونه", title_en="Sample clinic", fictional_brand_fa="نمونه", fictional_brand_en="Sample", style_key="minimal")

    def test_adapter_reuses_submission_idempotency_and_routes_clinic(self):
        url = "/fa/start/?type=clinic&sample=order-clinic&addons=support"
        data = {"submission_token": "order-adapter-token", "theme": "warm", "personality": "minimal", "features": ["booking"], "order_addons": ["webapp"]}
        first = self.client.post(url, data)
        second = self.client.post(url, data)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(urlsplit(first.url).path, "/fa/clinic-order/")
        self.assertEqual(first.url, second.url)
        self.assertEqual(DemoSelection.objects.count(), 1)
        self.assertIn("addons=webapp", first.url)
        self.assertNotIn("addons=support", first.url)
        page = self.client.get(first.url)
        self.assertIn("کلینیک نمونه", page.context["form"].initial["additional_notes"])
        self.assertContains(page, "انتخاب‌های شما")

    def test_foreign_session_cannot_read_specialist_demo_notes(self):
        session = self.client.session
        session.save()
        demo = DemoSelection.objects.create(template=self.demo, session_key="another-session", selections={"brand": "PRIVATE-BRAND"})
        page = self.client.get("/fa/clinic-order/", {"type": "clinic", "demo": str(demo.public_token)})
        self.assertNotIn("کلینیک نمونه", page.context["form"].initial.get("additional_notes", ""))
        self.assertNotContains(page, "PRIVATE-BRAND")

    def test_invalid_submission_does_not_create_demo(self):
        page = self.client.post("/fa/start/?type=clinic&sample=order-clinic", {"theme": "clay", "personality": "minimal"})
        self.assertEqual(page.status_code, 302)
        self.assertEqual(DemoSelection.objects.count(), 0)

    def test_edit_retry_keeps_addons_without_creating_duplicate(self):
        url = "/fa/start/?type=clinic&sample=order-clinic"
        data = {"submission_token": "edit-retry", "theme": "warm", "personality": "minimal", "order_addons": ["support"]}
        self.client.post(url, data)
        data["theme"] = "sage"
        retry = self.client.post(url, data)
        self.assertIn("stale=1", retry.url)
        self.assertIn("addons=support", retry.url)
        self.assertIn("type=clinic", retry.url)
        self.assertEqual(DemoSelection.objects.count(), 1)

    def test_general_prefill_maps_addon_and_ignores_personal_query(self):
        page = self.client.get("/en/contact/", {"type": "jewelry", "addons": "webapp,support", "name": "PRIVATE-NAME", "budget_range": "50_150", "evil": "PRIVATE-KEY"})
        initial = page.context["form"].initial
        self.assertEqual(initial["request_type"], "webapp")
        self.assertNotIn("budget_range", initial)
        self.assertNotIn("PRIVATE", initial.get("message", ""))
        self.assertEqual(page.context["order_summary"][0], "Jewellery boutique")
        self.assertNotContains(page, "انتخاب‌های شما")

    def test_crm_module_prefill_is_readable_not_new_form_fields(self):
        page = self.client.get("/fa/crm-order/", {"type": "crm", "modules": "customers,evil", "extensions": "ai", "phone": "PRIVATE-PHONE"})
        initial = page.context["form"].initial
        self.assertIn("مدیریت مشتریان", initial["additional_notes"])
        self.assertNotIn("evil", initial["additional_notes"])
        self.assertNotIn("phone", initial)

    def test_full_and_editor_preserve_allowlisted_context_only(self):
        for suffix in ("", "full/"):
            page = self.client.get("/en/projects/demos/order-clinic/" + suffix, {"addons": "support", "phone": "PRIVATE-PHONE"})
            self.assertContains(page, "data-order-query=")
            self.assertContains(page, "addons=support")
            self.assertNotContains(page, "PRIVATE-PHONE")

    def test_all_three_final_submissions_still_create_cases(self):
        from crm_orders.tests import valid_payload as crm_payload
        from clinic_orders.tests import valid_payload as clinic_payload
        from management_portal.models import CustomerCase
        from leads.models import Lead
        from crm_orders.models import CrmOrder
        from clinic_orders.models import ClinicOrder
        from django.contrib.contenttypes.models import ContentType
        lead_payload = {"name": "Test", "business_name": "Example", "email_or_telegram": "test@example.com", "phone": "", "request_type": "website", "service": "", "website_url": "", "budget_range": "50_150", "timeline": "one_three", "preferred_contact": "email", "message": "A sufficiently detailed test project request.", "privacy_accept": "on", "website": ""}
        for url, payload, model in (("/fa/contact/?type=corporate", lead_payload, Lead), ("/fa/crm-order/?type=crm", crm_payload(), CrmOrder), ("/fa/clinic-order/?type=clinic", clinic_payload(), ClinicOrder)):
            cache.clear()
            response = self.client.post(url, payload)
            self.assertEqual(response.status_code, 302, getattr(response, "context", None))
            record = model.objects.get()
            self.assertTrue(CustomerCase.objects.filter(source_content_type=ContentType.objects.get_for_model(model), source_object_id=record.pk).exists())
            self.assertEqual(self.client.get(response.url).status_code, 200)
            thanks = self.client.get(response.url)
            self.assertContains(thanks, 'class="order-completion"')
            self.assertContains(thanks, record.tracking_code)
