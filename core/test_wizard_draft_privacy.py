import re

from django.test import TestCase


class WizardDraftPrivacyTests(TestCase):
    FORMS = (
        ("/fa/contact/", {"request_type", "service", "budget_range", "timeline", "preferred_contact"}),
        ("/fa/crm-order/", {"organization_size", "primary_goals", "budget_range", "required_capabilities"}),
        ("/fa/clinic-order/", {"clinic_type", "primary_goals", "visit_modes", "payment_methods"}),
    )
    FORBIDDEN_FIELDS = {
        "name", "contact_name", "business_name", "organization_name", "clinic_name",
        "phone", "work_email", "email_or_telegram", "website", "website_url",
        "message", "current_process", "main_pain_points", "additional_notes",
    }

    def test_each_wizard_declares_a_separate_explicit_non_sensitive_allowlist(self):
        allowlists = []
        for path, expected_fields in self.FORMS:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                match = re.search(r'data-draft-fields="([^"]+)"', response.content.decode())
                self.assertIsNotNone(match)
                fields = set(match.group(1).split())
                self.assertTrue(expected_fields.issubset(fields))
                self.assertTrue(fields.isdisjoint(self.FORBIDDEN_FIELDS))
                allowlists.append(fields)

        self.assertNotEqual(allowlists[0], allowlists[1])
        self.assertNotEqual(allowlists[1], allowlists[2])

    def test_consent_copy_discloses_that_identity_and_free_text_are_not_saved(self):
        crm = self.client.get("/fa/crm-order/")
        clinic = self.client.get("/fa/clinic-order/")
        contact_en = self.client.get("/en/contact/")

        self.assertContains(crm, "نام فرد یا سازمان")
        self.assertContains(crm, "پاسخ‌های تشریحی ذخیره نمی‌شوند")
        self.assertContains(clinic, "نام کلینیک و فرد")
        self.assertContains(contact_en, "free-text messages are never saved")
