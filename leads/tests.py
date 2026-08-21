from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Lead


class LeadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("leads:contact") + "?lang=fa"
        self.payload = {
            "name": "آروین یزدانی", "business_name": "کسب‌وکار تست", "email_or_telegram": "test@example.com",
            "phone": "", "request_type": "webapp", "service": "", "website_url": "",
            "budget_range": "50_150", "timeline": "one_three", "preferred_contact": "email",
            "message": "این یک پیام تست معتبر برای ساخت پلتفرم است.", "privacy_accept": "on", "website": "",
        }

    def test_valid_submission_creates_lead_and_email(self):
        response = self.client.post(self.url, self.payload)
        lead = Lead.objects.get()
        self.assertRedirects(response, reverse("leads:thanks", args=[lead.tracking_code]) + "?lang=fa")
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(lead.status, "new")
        self.assertIsNotNone(lead.privacy_accepted_at)
        self.assertIn(lead.tracking_code, mail.outbox[0].subject)

    def test_enquiry_labels_and_steps_follow_page_language(self):
        fa_response = self.client.get(reverse("leads:contact") + "?lang=fa")
        self.assertContains(fa_response, "مشاوره اولیه رایگان")
        self.assertContains(fa_response, "تعهد آرویون")
        self.assertContains(fa_response, ">۰۱<", html=False)
        self.assertNotContains(fa_response, "FREE INITIAL CONSULTATION")
        self.assertNotContains(fa_response, "RVION PROMISE")

        en_response = self.client.get(reverse("leads:contact") + "?lang=en")
        self.assertContains(en_response, "FREE INITIAL CONSULTATION")
        self.assertContains(en_response, "RVION PROMISE")
        self.assertContains(en_response, ">01<", html=False)

    def test_honeypot_rejects_bot(self):
        self.payload["website"] = "https://spam.example"
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    def test_persian_phone_digits_are_accepted_and_normalized(self):
        self.payload["phone"] = "۰۹۱۲۲۰۹۰۷۹۷"
        self.client.post(self.url, self.payload)
        self.assertEqual(Lead.objects.get().phone, "09122090797")

    def test_rate_limit_blocks_second_submission(self):
        self.client.post(self.url, self.payload)
        self.payload["email_or_telegram"] = "second@example.com"
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 1)

    def test_privacy_consent_is_required(self):
        self.payload.pop("privacy_accept")
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lead.objects.count(), 0)

    def test_phone_is_required_when_phone_contact_is_selected(self):
        self.payload["preferred_contact"] = "phone"
        response = self.client.post(self.url, self.payload)
        self.assertContains(response, "برای تماس تلفنی، شماره تماس لازم است")
        self.assertEqual(Lead.objects.count(), 0)

    def test_service_query_prefills_enquiry_and_confirmation_hides_personal_data(self):
        from services.models import Service

        service = Service.objects.get(slug="corporate-website-design")
        page = self.client.get(self.url + f"&service={service.slug}")
        self.assertEqual(page.context["form"].initial["service"], service)
        self.assertEqual(page.context["form"].initial["request_type"], "website")
        self.payload["service"] = service.pk
        submitted = self.client.post(self.url, self.payload)
        lead = Lead.objects.get()
        confirmation = self.client.get(submitted.url)
        self.assertContains(confirmation, lead.tracking_code)
        self.assertContains(confirmation, service.title_fa)
        self.assertNotContains(confirmation, lead.email_or_telegram)
