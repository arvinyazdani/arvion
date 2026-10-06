from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import translation

from .models import Attempt, ExamEntitlement, Order
from .test_welcome_credit import make_exam


class PrestartGuidanceTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.user = get_user_model().objects.create_user(username="prestart@example.test", email="prestart@example.test")
        exam = make_exam("prestart-guidance")
        order = Order.objects.create(user=self.user, exam=exam, status="paid", amount_irr=0)
        self.entitlement = ExamEntitlement.objects.create(user=self.user, exam=exam, order=order)

    def test_reading_does_not_start_or_consume_the_attempt(self):
        self.client.force_login(self.user)
        for lang, text in (("fa", "زمان پاسخ مهم است"), ("en", "Response time matters")):
            response = self.client.get(f"/{lang}/assessments/entitlement/{self.entitlement.pk}/start/")
            self.assertContains(response, text)
            self.assertContains(response, 'name="guidance_read"')
            self.assertContains(response, 'type="checkbox" required')
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 1)
        self.assertFalse(Attempt.objects.exists())

    def test_another_account_cannot_read_the_guide(self):
        other = get_user_model().objects.create_user(username="otherprestart@example.test", email="otherprestart@example.test")
        self.client.force_login(other)
        response = self.client.get(f"/fa/assessments/entitlement/{self.entitlement.pk}/start/")
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_must_login(self):
        response = self.client.get(f"/fa/assessments/entitlement/{self.entitlement.pk}/start/")
        self.assertEqual(response.status_code, 302)
