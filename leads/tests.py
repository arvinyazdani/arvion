from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Lead


class LeadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("leads:contact") + "?lang=fa"
        self.payload = {"name": "آروین", "email_or_telegram": "test@example.com", "phone": "", "request_type": "project", "message": "این یک پیام تست معتبر است.", "website": ""}

    def test_valid_submission_creates_lead_and_email(self):
        response = self.client.post(self.url, self.payload)
        self.assertRedirects(response, "/contact/?lang=fa&submitted=1")
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

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
