"""V2.1-C1: the leads-contact page's exposure of the account-bound server
draft API to the wizard — safe data attributes, the mandatory bilingual
disclosure, and the Django-error-rerender step marker. No JavaScript
behavior is exercised here (that is covered by manual browser verification);
these tests only check what the server renders into the page."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from leads.form_draft_service import save_draft_fields
from leads.models import FormDraft

User = get_user_model()

CONTACT_URL = reverse("leads:contact")

FA_NOTICE = "گزینه‌های غیرحساس این فرم در حساب شما ذخیره می‌شوند"
EN_NOTICE = "Non-sensitive selections from this form are saved to your account"


def make_customer(suffix="a"):
    return User.objects.create_user(
        username=f"contact-ui-customer-{suffix}@example.com", email=f"contact-ui-customer-{suffix}@example.com",
        password="x", is_active=True,
    )


def make_staff(suffix="a"):
    return User.objects.create_user(
        username=f"contact-ui-staff-{suffix}@example.com", email=f"contact-ui-staff-{suffix}@example.com",
        password="x", is_active=True, is_staff=True,
    )


class ServerDraftDataAttributeTests(TestCase):
    def test_guest_sees_no_server_draft_data_attribute(self):
        response = self.client.get(CONTACT_URL + "?lang=fa")
        content = response.content.decode("utf-8")
        self.assertNotIn("data-server-draft", content)
        self.assertNotIn("data-draft-url", content)
        self.assertNotIn("data-draft-delete-url", content)
        self.assertNotIn("data-login-url", content)
        self.assertNotIn("wizard-server-draft-notice", content)
        # The old per-device consent box is still the guest's experience.
        self.assertIn("data-draft-consent", content)

    def test_authenticated_customer_sees_safe_reversed_url_attributes(self):
        customer = make_customer()
        self.client.force_login(customer)

        response = self.client.get(CONTACT_URL + "?lang=fa")

        content = response.content.decode("utf-8")
        self.assertContains(response, 'data-server-draft="1"')
        self.assertContains(response, f'data-draft-url="{reverse("leads:draft")}"')
        self.assertContains(response, f'data-draft-delete-url="{reverse("leads:draft_delete")}"')
        self.assertContains(response, f'data-login-url="{reverse("accounts:login")}"')
        self.assertContains(response, 'data-lang="fa"')
        # The legacy per-device consent box must not appear for an
        # authenticated customer — replaced by the mandatory disclosure.
        self.assertNotIn("data-draft-consent", content)
        self.assertIn("wizard-server-draft-notice", content)

    def test_staff_gets_no_server_draft_mode(self):
        staff = make_staff()
        self.client.force_login(staff)

        response = self.client.get(CONTACT_URL + "?lang=fa")

        content = response.content.decode("utf-8")
        self.assertNotIn("data-server-draft", content)
        self.assertNotIn("data-draft-url", content)
        self.assertNotIn("data-draft-delete-url", content)
        self.assertNotIn("wizard-server-draft-notice", content)
        self.assertIn("data-draft-consent", content)

    def test_superuser_gets_no_server_draft_mode(self):
        superuser = User.objects.create_superuser(
            username="contact-ui-superuser@example.com", email="contact-ui-superuser@example.com", password="x",
        )
        self.client.force_login(superuser)

        response = self.client.get(CONTACT_URL + "?lang=fa")

        self.assertNotIn("data-server-draft", response.content.decode("utf-8"))

    def test_no_sensitive_token_or_id_in_html_even_with_an_existing_draft(self):
        customer = make_customer()
        draft, _ = save_draft_fields(
            owner=customer, form_type="leads_contact", fields={"request_type": "webapp"},
            current_step=1, expected_revision=0,
        )
        self.client.force_login(customer)

        response = self.client.get(CONTACT_URL + "?lang=fa")
        content = response.content.decode("utf-8")

        # The page never renders draft content server-side at all in this
        # phase (restore happens client-side via a GET the JS makes after
        # load) — so none of the draft's own identifiers can leak here. A
        # bare numeric pk is not itself checked (small integers like "1"
        # collide harmlessly with unrelated page content, e.g. asset
        # version query strings) — instead this checks for the specific
        # attribute shapes that would actually leak an id, plus every real
        # secret token name.
        self.assertNotIn("data-draft-id", content)
        self.assertNotIn("data-owner-id", content)
        self.assertNotIn("data-user-id", content)
        self.assertNotIn(f'data-draft-url="{reverse("leads:draft")}{draft.pk}', content)
        self.assertNotIn("session_key", content)
        self.assertNotIn("public_token", content)
        # V2.1-D intentionally renders one hidden, non-secret idempotency
        # field literally named "final_submission_token" — that is not a
        # leak, so this checks for the *internal DB field/value* leaking
        # instead of the (now legitimate) substring "submission_token".
        self.assertNotIn("data-submission-token", content)
        self.assertIsNone(draft.submission_token)
        self.assertEqual(FormDraft.objects.filter(owner=customer).count(), 1)

    def test_final_submission_token_is_present_only_for_authenticated_non_staff(self):
        customer = make_customer(suffix="fst")
        self.client.force_login(customer)
        response = self.client.get(CONTACT_URL + "?lang=fa")
        self.assertContains(response, 'name="final_submission_token"')

        self.client.logout()
        guest_response = self.client.get(CONTACT_URL + "?lang=fa")
        self.assertNotContains(guest_response, "final_submission_token")

        staff = make_staff(suffix="fst")
        self.client.force_login(staff)
        staff_response = self.client.get(CONTACT_URL + "?lang=fa")
        self.assertNotContains(staff_response, "final_submission_token")

    def test_fa_page_shows_only_fa_notice_text_en_page_shows_only_en(self):
        customer = make_customer()
        self.client.force_login(customer)

        fa_response = self.client.get(CONTACT_URL + "?lang=fa")
        fa_content = fa_response.content.decode("utf-8")
        self.assertIn(FA_NOTICE, fa_content)
        self.assertNotIn(EN_NOTICE, fa_content)

        en_response = self.client.get(CONTACT_URL + "?lang=en")
        en_content = en_response.content.decode("utf-8")
        self.assertIn(EN_NOTICE, en_content)
        self.assertNotIn(FA_NOTICE, en_content)


class ErrorRerenderStepMarkerTests(TestCase):
    def setUp(self):
        self.url = CONTACT_URL + "?lang=fa"
        self.payload = {
            "name": "آروین یزدانی", "business_name": "", "email_or_telegram": "test@example.com",
            "phone": "", "request_type": "webapp", "service": "", "website_url": "",
            "budget_range": "50_150", "timeline": "one_three", "preferred_contact": "email",
            "message": "این یک پیام تست معتبر برای ساخت پلتفرم است.", "privacy_accept": "", "website": "",
        }

    def test_step3_field_error_marks_step_3(self):
        # privacy_accept is a step-3 field; omitting it must land the error
        # marker on step 3, matching the CRM/clinic wizard's own convention.
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-error-step="3"')

    def test_step1_field_error_marks_step_1(self):
        self.payload["privacy_accept"] = "on"
        self.payload["request_type"] = "not-a-real-choice"
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-error-step="1"')

    def test_valid_submission_has_no_error_step_marker(self):
        self.payload["privacy_accept"] = "on"
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 302)
