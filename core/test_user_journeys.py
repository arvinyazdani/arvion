import re
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from assessments.models import (
    Attempt, AttemptResult, Choice, Exam, ExamEntitlement, ExamSection,
    ExamVersion, ManualPaymentSubmission, Order, Question, Skill,
)
from assessments.services import approve_manual_payment
from core.jalali import format_jalali
from leads.models import Lead


class PublicUserJourneyTests(TestCase):
    def make_english_assessment(self):
        exam = Exam.objects.create(
            slug="english-placement-a1-c1",
            title_fa="آزمون تعیین سطح زبان انگلیسی",
            title_en="English placement assessment",
            description_fa="ارزیابی مهارت زبان",
            description_en="English skill assessment",
            language_mode="en",
            question_count=2,
            duration_minutes=10,
            price_irr=2_000_000,
        )
        version = ExamVersion.objects.create(
            exam=exam, version=1, is_published=True, published_at=timezone.now(),
        )
        section = ExamSection.objects.create(
            version=version, code="grammar", title_fa="دستور زبان",
            title_en="Grammar", question_count=2,
        )
        skill = Skill.objects.create(
            exam=exam, code="grammar", title_fa="دستور زبان", title_en="Grammar",
        )
        for index in range(2):
            question = Question.objects.create(
                version=version, section=section, skill=skill,
                prompt_fa=f"سؤال {index + 1}", prompt_en=f"Question {index + 1}",
                explanation_fa="توضیح پاسخ", explanation_en="Answer explanation",
            )
            for choice_index in range(4):
                Choice.objects.create(
                    question=question,
                    text_fa=f"گزینه {choice_index + 1}",
                    text_en=f"Choice {choice_index + 1}",
                    is_correct=choice_index == 0,
                    display_order=choice_index,
                )
        return exam

    def test_visitor_can_register_and_reach_private_dashboard(self):
        response = self.client.post(reverse("accounts:register") + "?lang=en", {
            "first_name": "Journey", "last_name": "Tester",
            "email": "journey@example.com",
            "mobile": "09121234567",
            "password1": "A-secure-journey-password-42",
            "password2": "A-secure-journey-password-42",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/dashboard.html")
        user = User.objects.get(email="journey@example.com")
        self.assertTrue(user.is_active)
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

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_customer_completes_english_assessment_from_home_to_result(self):
        exam = self.make_english_assessment()
        home = self.client.get("/fa/")
        briefing_url = reverse("assessments:briefing", args=[exam.slug])
        detail_url = reverse("assessments:detail", args=[exam.slug])
        purchase_url = reverse("assessments:create_order", args=[exam.slug])
        self.assertContains(home, briefing_url)
        self.assertContains(self.client.get(briefing_url), "مشاهده قیمت و ادامه پرداخت")
        self.assertContains(self.client.get(detail_url), "ورود و ادامه پرداخت")

        requires_login = self.client.post(purchase_url)
        self.assertIn(reverse("accounts:login"), requires_login.url)
        next_url = parse_qs(urlsplit(requires_login.url).query)["next"][0]
        register_url = reverse("accounts:register")
        login_page = self.client.get(requires_login.url)
        self.assertContains(login_page, f"{register_url}?next=")

        registration = {
            "first_name": "Journey", "last_name": "Candidate",
            "email": "journey-assessment@example.com", "mobile": "09121234567",
            "password1": "A-secure-journey-password-42",
            "password2": "A-secure-journey-password-42", "next": next_url,
        }
        registered = self.client.post(register_url, registration)
        self.assertRedirects(registered, detail_url, fetch_redirect_response=False)
        self.assertFalse(Order.objects.exists())

        ordered = self.client.post(purchase_url)
        order = Order.objects.get(user__email=registration["email"], exam=exam)
        self.assertEqual(ordered.url, f"{reverse('assessments:checkout', args=[order.pk])}?lang=fa")
        now = timezone.localtime()
        submitted = self.client.post(
            reverse("assessments:manual_payment_submit", args=[order.pk]),
            {
                "payer_name": "Journey Candidate", "reference_number": "JOURNEY123",
                "payment_date": format_jalali(now.date()),
                "payment_time": now.strftime("%H:%M"), "note": "", "accept_terms": "on",
            },
        )
        self.assertEqual(submitted.status_code, 302)
        payment = ManualPaymentSubmission.objects.get(order=order)
        self.assertFalse(ExamEntitlement.objects.filter(order=order).exists())

        approve_manual_payment(payment.pk, automatic=True, review_note="journey test")
        entitlement = ExamEntitlement.objects.get(order=order)
        status = self.client.get(reverse("assessments:manual_payment_status", args=[order.pk]))
        self.assertTrue(status.json()["ready"])

        started = self.client.post(reverse("assessments:start_attempt", args=[entitlement.pk]))
        self.assertIn("/attempt/", started.url, started.url)
        attempt = Attempt.objects.get(entitlement=entitlement)
        self.assertEqual(started.url, f"{attempt.get_absolute_url()}?lang=fa")
        for item in attempt.attempt_questions.select_related("question"):
            correct = item.question.choices.get(is_correct=True)
            saved = self.client.post(
                reverse("assessments:save_answer", args=[attempt.pk, item.pk]),
                {"choice": correct.pk}, HTTP_ACCEPT="application/json",
            )
            self.assertEqual(saved.status_code, 200)
        review = self.client.get(reverse("assessments:attempt_review", args=[attempt.pk]))
        self.assertContains(review, "به همه سؤال‌ها پاسخ داده‌ای")
        finished = self.client.post(
            reverse("assessments:finish_attempt", args=[attempt.pk]),
            {"confirm_submission": "yes"},
        )
        result = AttemptResult.objects.get(attempt=attempt)
        self.assertEqual(finished.url, f"{reverse('assessments:result', args=[result.pk])}?lang=fa")
        self.assertEqual(result.percentage, 100)
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "completed")
