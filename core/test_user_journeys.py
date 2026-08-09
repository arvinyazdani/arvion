import re

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from leads.models import Lead


class PublicUserJourneyTests(TestCase):
    def test_visitor_can_register_verify_and_reach_private_dashboard(self):
        response = self.client.post(reverse("accounts:register") + "?lang=en", {
            "first_name": "Journey", "last_name": "Tester",
            "email": "journey@example.com",
            "password1": "A-secure-journey-password-42",
            "password2": "A-secure-journey-password-42",
        })
        self.assertRedirects(response, reverse("accounts:verification_sent") + "?lang=en")
        verification_path = re.search(r"http://testserver([^\s]+)", mail.outbox[0].body).group(1)

        verified = self.client.get(verification_path, follow=True)

        self.assertEqual(verified.status_code, 200)
        self.assertTemplateUsed(verified, "accounts/dashboard.html")
        user = User.objects.get(email="journey@example.com")
        self.assertTrue(user.email_verified)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_visitor_can_submit_general_enquiry_and_use_reference_page(self):
        response = self.client.post(reverse("leads:contact") + "?lang=fa", {
            "request_type": "consultation", "business_name": "سازمان نمونه",
            "name": "کاربر آزمایشی", "phone": "09121234567",
            "email_or_telegram": "customer@example.com", "preferred_contact": "phone",
            "budget_range": "unsure", "timeline": "flexible",
            "message": "برای تحلیل و طراحی سامانه سازمانی نیاز به مشاوره داریم.",
            "privacy_accept": "on", "website": "",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        lead = Lead.objects.get()
        self.assertContains(response, lead.tracking_code)
        self.assertTemplateUsed(response, "leads/thanks.html")

