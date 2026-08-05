from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from .models import (
    Attempt, AttemptQuestion, AttemptResult, Certificate, Choice, Exam,
    ExamEntitlement, ExamSection, ExamVersion, IntegrityEvent, Order,
    PaymentTransaction, Question, Skill,
)
from .services import ExamContentError, score_attempt, start_attempt, verify_sandbox_payment


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


class AssessmentEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="candidate@example.com", email="candidate@example.com",
            password="test-password-42", is_active=True, email_verified=True,
        )
        self.exam = Exam.objects.create(
            slug="engine-test", title_fa="آزمون موتور", title_en="Engine test",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
            question_count=2, duration_minutes=10,
        )
        self.version = ExamVersion.objects.create(
            exam=self.exam, version=1, is_published=True, published_at=timezone.now(),
        )
        self.section = ExamSection.objects.create(
            version=self.version, code="core", title_fa="پایه", title_en="Core",
            question_count=2,
        )
        self.skill = Skill.objects.create(
            exam=self.exam, code="python", title_fa="پایتون", title_en="Python",
        )
        self.questions = [self.make_question(index) for index in range(3)]
        self.order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=self.exam.price_irr, status="paid",
        )
        self.entitlement = ExamEntitlement.objects.create(
            user=self.user, exam=self.exam, order=self.order, attempts_remaining=1,
        )

    def make_question(self, index):
        question = Question.objects.create(
            version=self.version, section=self.section, skill=self.skill,
            prompt_fa=f"سؤال {index}", prompt_en=f"Question {index}", difficulty=3,
        )
        for choice_index in range(4):
            Choice.objects.create(
                question=question, text_fa=f"گزینه {choice_index}",
                text_en=f"Choice {choice_index}", is_correct=choice_index == 0,
                display_order=choice_index,
            )
        return question

    def start(self):
        return start_attempt(self.entitlement.pk, self.user)[0]

    def test_start_builds_randomized_snapshot_and_consumes_entitlement(self):
        attempt, created = start_attempt(self.entitlement.pk, self.user)
        self.assertTrue(created)
        self.assertEqual(attempt.attempt_questions.count(), 2)
        self.assertEqual(len(set(attempt.attempt_questions.values_list("question_id", flat=True))), 2)
        self.assertTrue(all(len(row.choice_order) == 4 for row in attempt.attempt_questions.all()))
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 0)

    def test_start_attempt_has_bounded_query_count(self):
        with CaptureQueriesContext(connection) as queries:
            start_attempt(self.entitlement.pk, self.user)
        self.assertLessEqual(len(queries), 15)

    def test_start_is_idempotent(self):
        first, _ = start_attempt(self.entitlement.pk, self.user)
        second, created = start_attempt(self.entitlement.pk, self.user)
        self.assertFalse(created)
        self.assertEqual(first.pk, second.pk)
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 0)

    def test_invalid_question_pool_rolls_back(self):
        self.section.question_count = 4
        self.section.save()
        with self.assertRaises(ExamContentError):
            start_attempt(self.entitlement.pk, self.user)
        self.assertFalse(Attempt.objects.exists())
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 1)

    def test_attempt_page_is_private_to_owner(self):
        attempt = self.start()
        other = User.objects.create_user(username="other2@example.com", email="other2@example.com", password="test")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("assessments:attempt", args=[attempt.pk])).status_code, 404)

    def test_answer_is_saved_and_rejects_foreign_choice(self):
        attempt = self.start()
        item = attempt.attempt_questions.first()
        valid_choice = item.question.choices.first()
        foreign_question = next(question for question in self.questions if question.pk != item.question_id)
        self.client.force_login(self.user)
        response = self.client.post(reverse("assessments:save_answer", args=[attempt.pk, item.pk]), {"choice": valid_choice.pk})
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.selected_choice, valid_choice)
        response = self.client.post(reverse("assessments:save_answer", args=[attempt.pk, item.pk]), {"choice": foreign_question.choices.first().pk})
        self.assertEqual(response.status_code, 404)

    def test_integrity_event_is_recorded_and_score_reduced(self):
        attempt = self.start()
        self.client.force_login(self.user)
        response = self.client.post(reverse("assessments:integrity_event", args=[attempt.pk]), {"event_type": "tab_hidden"})
        self.assertEqual(response.status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.integrity_score, 98)
        self.assertTrue(IntegrityEvent.objects.filter(attempt=attempt, event_type="tab_hidden").exists())

    def test_integrity_events_are_deduplicated_and_deduction_is_capped(self):
        attempt = self.start()
        self.client.force_login(self.user)
        url = reverse("assessments:integrity_event", args=[attempt.pk])
        first = self.client.post(url, {"event_type": "tab_hidden"})
        duplicate = self.client.post(url, {"event_type": "tab_hidden"})
        self.assertEqual(first.status_code, 200)
        self.assertTrue(duplicate.json()["deduplicated"])
        self.assertEqual(IntegrityEvent.objects.filter(attempt=attempt).count(), 1)
        for _ in range(9):
            IntegrityEvent.objects.filter(attempt=attempt).update(
                created_at=timezone.now() - timedelta(seconds=20)
            )
            self.client.post(url, {"event_type": "tab_hidden"})
        attempt.refresh_from_db()
        self.assertEqual(attempt.integrity_score, 90)

    def test_finish_submits_attempt(self):
        attempt = self.start()
        self.client.force_login(self.user)
        response = self.client.post(reverse("assessments:finish_attempt", args=[attempt.pk]))
        result = AttemptResult.objects.get(attempt=attempt)
        self.assertRedirects(response, reverse("assessments:result", args=[result.pk]) + "?lang=fa")
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "completed")
        self.assertTrue(Certificate.objects.filter(result=result).exists())

    def test_expired_attempt_cannot_accept_answers(self):
        attempt = self.start()
        attempt.expires_at = timezone.now()
        attempt.save(update_fields=["expires_at"])
        item = attempt.attempt_questions.first()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("assessments:save_answer", args=[attempt.pk, item.pk]),
            {"choice": item.question.choices.first().pk},
        )
        self.assertEqual(response.status_code, 409)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "expired")

    def test_deterministic_scoring_builds_skill_result(self):
        attempt = self.start()
        rows = list(attempt.attempt_questions.all())
        rows[0].selected_choice = rows[0].question.choices.get(is_correct=True)
        rows[0].save()
        rows[1].selected_choice = rows[1].question.choices.filter(is_correct=False).first()
        rows[1].save()
        attempt.status = "submitted"
        attempt.save()
        result, created = score_attempt(attempt.pk)
        self.assertTrue(created)
        self.assertEqual(result.percentage, 50)
        self.assertEqual(result.correct_count, 1)
        self.assertEqual(result.incorrect_count, 1)
        self.assertEqual(result.level_code, "junior")
        self.assertEqual(result.skill_results.get().percentage, 50)

    def test_scoring_is_idempotent(self):
        attempt = self.start()
        attempt.status = "submitted"
        attempt.save()
        first, _ = score_attempt(attempt.pk)
        second, created = score_attempt(attempt.pk)
        self.assertFalse(created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(AttemptResult.objects.count(), 1)

    def test_result_is_private_but_certificate_is_verifiable(self):
        attempt = self.start()
        attempt.status = "submitted"
        attempt.save()
        result, _ = score_attempt(attempt.pk)
        other = User.objects.create_user(username="viewer@example.com", email="viewer@example.com", password="test")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("assessments:result", args=[result.pk])).status_code, 404)
        certificate_response = self.client.get(reverse("assessments:certificate", args=[result.certificate.verification_code]))
        self.assertEqual(certificate_response.status_code, 200)
        self.assertContains(certificate_response, result.certificate.verification_code)
        self.assertNotContains(certificate_response, self.user.email)

    def test_complete_candidate_journey_from_start_to_report(self):
        self.client.force_login(self.user)
        start_response = self.client.post(reverse("assessments:start_attempt", args=[self.entitlement.pk]))
        attempt = Attempt.objects.get(entitlement=self.entitlement)
        self.assertRedirects(start_response, attempt.get_absolute_url() + "?lang=fa")
        self.assertContains(self.client.get(attempt.get_absolute_url()), "سؤال 1 / 2")
        for item in attempt.attempt_questions.select_related("question"):
            choice = item.question.choices.get(is_correct=True)
            answer_response = self.client.post(
                reverse("assessments:save_answer", args=[attempt.pk, item.pk]), {"choice": choice.pk}
            )
            self.assertEqual(answer_response.status_code, 200)
        finish_response = self.client.post(reverse("assessments:finish_attempt", args=[attempt.pk]))
        result = AttemptResult.objects.get(attempt=attempt)
        self.assertRedirects(finish_response, reverse("assessments:result", args=[result.pk]) + "?lang=fa")
        report = self.client.get(reverse("assessments:result", args=[result.pk]))
        self.assertContains(report, "100")
        self.assertEqual(result.percentage, 100)
