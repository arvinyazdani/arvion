import threading
from datetime import timedelta
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import close_old_connections, connection
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import translation
from django.utils import timezone

from .models import Attempt, Choice, Exam, ExamEntitlement, ExamSection, ExamVersion, Order, PaymentTransaction, Question, Skill, WelcomeAssessmentCredit
from .services import PaymentVerificationError, redeem_welcome_assessment, start_attempt


def make_exam(slug="welcome-english"):
    return Exam.objects.create(slug=slug, title_fa="آزمون زبان", title_en="English assessment",
        description_fa="توضیح", description_en="Description", language_mode="en", price_irr=2_000_000)


@override_settings(ASSESSMENT_FREE_CHECKOUT=False)
class WelcomeAssessmentTests(TestCase):
    def setUp(self):
        cache.clear()
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.user = get_user_model().objects.create_user(username="welcome@example.test", email="welcome@example.test")
        self.exam = make_exam()

    def test_registration_issues_credit_only_for_a_new_account(self):
        response = self.client.post(reverse("accounts:register"), {
            "email": "newwelcome@example.test", "mobile": "09123456789",
            "first_name": "Test", "last_name": "Customer",
            "password1": "Strong-welcome-test-827!", "password2": "Strong-welcome-test-827!",
        })
        self.assertEqual(response.status_code, 302)
        new = get_user_model().objects.get(email="newwelcome@example.test")
        self.assertEqual(WelcomeAssessmentCredit.objects.filter(user=new, order__isnull=True).count(), 1)
        self.assertFalse(WelcomeAssessmentCredit.objects.filter(user=self.user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), new.pk)

    def test_one_credit_across_exams_and_same_exam_replay(self):
        credit = WelcomeAssessmentCredit.objects.create(user=self.user)
        order, created = redeem_welcome_assessment(user=self.user, exam=self.exam)
        replay, repeated = redeem_welcome_assessment(user=self.user, exam=self.exam)
        self.assertTrue(created)
        self.assertFalse(repeated)
        self.assertEqual(order.pk, replay.pk)
        with self.assertRaises(PaymentVerificationError):
            redeem_welcome_assessment(user=self.user, exam=make_exam("welcome-python"))
        credit.refresh_from_db()
        self.assertEqual(credit.order_id, order.pk)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.gateway, "welcome_trial")
        self.assertEqual(order.status, "paid")
        self.assertEqual(order.amount_irr, 0)
        self.assertEqual(order.discount_percent, 100)
        self.assertEqual(ExamEntitlement.objects.get().attempts_remaining, 1)
        self.assertEqual(PaymentTransaction.objects.get().amount_irr, 0)

    def test_terms_required_and_no_payment_or_credit_change_on_rejection(self):
        credit = WelcomeAssessmentCredit.objects.create(user=self.user)
        self.client.force_login(self.user)
        response = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]), {"use_welcome_credit": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.exists())
        credit.refresh_from_db()
        self.assertIsNone(credit.order_id)
        self.client.post(reverse("assessments:create_order", args=[self.exam.slug]), {"use_welcome_credit": "yes", "accept_terms": "yes"})
        self.assertEqual(ExamEntitlement.objects.count(), 1)

    def test_no_credit_staff_inactive_and_inactive_exam_cannot_redeem(self):
        with self.assertRaises(PaymentVerificationError):
            redeem_welcome_assessment(user=self.user, exam=self.exam)
        WelcomeAssessmentCredit.objects.create(user=self.user)
        for attr in ("is_staff", "is_superuser"):
            setattr(self.user, attr, True)
            with self.assertRaises(PaymentVerificationError):
                redeem_welcome_assessment(user=self.user, exam=self.exam)
            setattr(self.user, attr, False)
        self.user.is_active = False
        with self.assertRaises(PaymentVerificationError):
            redeem_welcome_assessment(user=self.user, exam=self.exam)
        self.user.is_active = True
        self.exam.is_active = False
        with self.assertRaises(PaymentVerificationError):
            redeem_welcome_assessment(user=self.user, exam=self.exam)
        self.assertFalse(Order.objects.exists())

    def test_free_post_does_not_grant_an_old_user_access(self):
        self.client.force_login(self.user)
        self.client.post(reverse("assessments:create_order", args=[self.exam.slug]), {"use_welcome_credit": "yes", "accept_terms": "yes"})
        self.assertFalse(Order.objects.exists())
        self.assertFalse(ExamEntitlement.objects.exists())

    def test_existing_pending_order_and_regular_checkout_are_unchanged(self):
        WelcomeAssessmentCredit.objects.create(user=self.user)
        pending = Order.objects.create(user=self.user, exam=self.exam, amount_irr=2_000_000, gateway="card_transfer")
        free, _ = redeem_welcome_assessment(user=self.user, exam=self.exam)
        pending.refresh_from_db()
        self.assertEqual(pending.amount_irr, 2_000_000)
        self.assertEqual(pending.status, "pending")
        self.assertNotEqual(pending.pk, free.pk)

    def test_fault_rolls_back_and_credit_can_be_retried(self):
        credit = WelcomeAssessmentCredit.objects.create(user=self.user)
        with patch("assessments.services.ExamEntitlement.objects.get_or_create", side_effect=RuntimeError("injected")):
            with self.assertRaises(RuntimeError):
                redeem_welcome_assessment(user=self.user, exam=self.exam)
        credit.refresh_from_db()
        self.assertIsNone(credit.order_id)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(PaymentTransaction.objects.exists())
        redeem_welcome_assessment(user=self.user, exam=self.exam)
        self.assertEqual(ExamEntitlement.objects.count(), 1)

    def test_credit_grants_one_start_and_revocation_does_not_renew_it(self):
        WelcomeAssessmentCredit.objects.create(user=self.user)
        self.exam.question_count = 1
        self.exam.save()
        version = ExamVersion.objects.create(exam=self.exam, version=1, is_published=True)
        section = ExamSection.objects.create(version=version, code="grammar", title_fa="گرامر", title_en="Grammar", question_count=1)
        skill = Skill.objects.create(exam=self.exam, code="grammar", title_fa="گرامر", title_en="Grammar")
        question = Question.objects.create(version=version, section=section, skill=skill, prompt_fa="نمونه", prompt_en="Example")
        Choice.objects.create(question=question, text_fa="الف", text_en="A", is_correct=True)
        Choice.objects.create(question=question, text_fa="ب", text_en="B")
        Choice.objects.create(question=question, text_fa="ج", text_en="C")
        Choice.objects.create(question=question, text_fa="د", text_en="D")
        order, _ = redeem_welcome_assessment(user=self.user, exam=self.exam)
        entitlement = ExamEntitlement.objects.get(order=order)
        attempt, created = start_attempt(entitlement.pk, self.user)
        resumed, repeated = start_attempt(entitlement.pk, self.user)
        self.assertTrue(created)
        self.assertFalse(repeated)
        self.assertEqual(attempt.pk, resumed.pk)
        entitlement.refresh_from_db()
        self.assertEqual(entitlement.attempts_remaining, 0)
        self.assertEqual(Attempt.objects.count(), 1)
        from django.utils import timezone
        entitlement.revoked_at = timezone.now()
        entitlement.save()
        redeem_welcome_assessment(user=self.user, exam=self.exam)
        entitlement.refresh_from_db()
        self.assertIsNotNone(entitlement.revoked_at)
        self.assertEqual(ExamEntitlement.objects.count(), 1)

    def test_bilingual_discovery_and_consumed_credit_hides_offer(self):
        WelcomeAssessmentCredit.objects.create(user=self.user)
        self.client.force_login(self.user)
        for lang, label in (("fa", "فعال‌سازی یک نوبت رایگان"), ("en", "Activate one free attempt")):
            self.assertContains(self.client.get(f"/{lang}/assessments/{self.exam.slug}/"), label)
        redeem_welcome_assessment(user=self.user, exam=self.exam)
        self.assertNotContains(self.client.get(f"/en/assessments/{self.exam.slug}/"), "Activate one free attempt")

    def test_briefing_explains_welcome_gift_without_revealing_the_price(self):
        for lang, label in (("fa", "تخفیف ۱۰۰٪"), ("en", "100% welcome discount")):
            response = self.client.get(f"/{lang}/assessments/{self.exam.slug}/about/")
            self.assertContains(response, label)
            self.assertNotContains(response, "2,000,000")
            self.assertNotContains(response, "فعال‌سازی یک نوبت رایگان</button>")

    def test_paid_promotion_explanation_matches_server_quote_and_expires(self):
        self.client.force_login(self.user)
        with override_settings(ASSESSMENT_PROMOTION_SLUG=self.exam.slug,
                               ASSESSMENT_PROMOTION_PRICE_IRR=900_000,
                               ASSESSMENT_PROMOTION_ENDS_AT=timezone.now() + timedelta(hours=1)):
            self.assertContains(self.client.get(f"/fa/assessments/{self.exam.slug}/"), "۵۵٪ کمتر")
            self.assertContains(self.client.get(f"/en/assessments/{self.exam.slug}/"), "55% off")
        with override_settings(ASSESSMENT_PROMOTION_SLUG=self.exam.slug,
                               ASSESSMENT_PROMOTION_ENDS_AT=timezone.now() - timedelta(seconds=1)):
            self.assertNotContains(self.client.get(f"/en/assessments/{self.exam.slug}/"), "Purchase offer:")


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class WelcomeCreditRaceTests(TransactionTestCase):
    def test_simultaneous_different_exams_grant_exactly_one_credit(self):
        user = get_user_model().objects.create_user(username="racewelcome@example.test")
        WelcomeAssessmentCredit.objects.create(user=user)
        exams = [make_exam("race-one"), make_exam("race-two")]
        barrier = threading.Barrier(2)
        outcomes, errors = [], []
        def redeem(exam):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    redeem_welcome_assessment(user=user, exam=exam)
                    outcomes.append("granted")
                except PaymentVerificationError:
                    outcomes.append("used")
            except Exception as error:
                errors.append(error)
            finally:
                close_old_connections()
        threads = [threading.Thread(target=redeem, args=[exam]) for exam in exams]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=20)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(errors, [])
        self.assertCountEqual(outcomes, ["granted", "used"])
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(ExamEntitlement.objects.count(), 1)
