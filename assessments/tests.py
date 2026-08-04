from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Exam, ExamEntitlement, Order, PaymentTransaction
from .services import verify_sandbox_payment


User = get_user_model()


class AssessmentCommerceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="buyer@example.com",
            email="buyer@example.com",
            password="test-password-42",
            is_active=True,
            email_verified=True,
        )
        self.exam = Exam.objects.create(
            slug="python-test",
            title_fa="آزمون پایتون",
            title_en="Python test",
            description_fa="توضیح آزمون",
            description_en="Assessment description",
            language_mode="bilingual",
            price_irr=500_000,
        )

    def test_catalog_is_public(self):
        response = self.client.get(reverse("assessments:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "آزمون پایتون")

    def test_order_requires_login(self):
        response = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_order_price_is_copied_from_exam_on_server(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]), {"amount_irr": 1})
        order = Order.objects.get()
        self.assertEqual(order.amount_irr, 500_000)
        self.assertRedirects(response, reverse("assessments:checkout", args=[order.pk]) + "?lang=fa")

    def test_verified_payment_creates_exactly_one_entitlement(self):
        order = Order.objects.create(user=self.user, exam=self.exam, amount_irr=self.exam.price_irr)
        first_order, created = verify_sandbox_payment(order.pk)
        second_order, created_again = verify_sandbox_payment(order.pk)
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first_order.status, "paid")
        self.assertEqual(second_order.status, "paid")
        self.assertEqual(ExamEntitlement.objects.count(), 1)
        self.assertEqual(PaymentTransaction.objects.filter(status="verified").count(), 1)

    def test_checkout_is_private_to_order_owner(self):
        other = User.objects.create_user(username="other@example.com", email="other@example.com", password="test", is_active=True)
        order = Order.objects.create(user=other, exam=self.exam, amount_irr=self.exam.price_irr)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("assessments:checkout", args=[order.pk])).status_code, 404)

    def test_inactive_exam_cannot_be_purchased(self):
        self.exam.is_active = False
        self.exam.save()
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse("assessments:create_order", args=[self.exam.slug])).status_code, 404)

    def test_daily_order_limit_is_enforced(self):
        self.client.force_login(self.user)
        for _ in range(5):
            Order.objects.create(user=self.user, exam=self.exam, amount_irr=self.exam.price_irr)
        response = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))
        self.assertRedirects(response, self.exam.get_absolute_url() + "?lang=fa")
        self.assertEqual(Order.objects.count(), 5)
