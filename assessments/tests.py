from datetime import timedelta
from pathlib import Path
import random
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from core.jalali import format_jalali

from .models import (
    Attempt, AttemptQuestion, AttemptResult, Certificate, Choice, Exam,
    ExamEntitlement, ExamSection, ExamVersion, IntegrityEvent, Order,
    ManualPaymentSubmission, PaymentTransaction, Question, Skill, SupportTicket,
)
from .admin_exports import export_orders, export_results, export_tickets, mark_tickets_in_review, mark_tickets_resolved
from .integrity import assess_event
from .services import (
    AttemptLimitError, ExamContentError, PaymentVerificationError, _choose_section_questions, finalize_expired_attempt, score_attempt, start_attempt,
    verify_gateway_payment, verify_sandbox_payment,
)


User = get_user_model()

ASSESSMENT_STATIC_ROOT = Path(__file__).resolve().parent / "static" / "assessments"


class AssessmentUISystemTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.styles = (ASSESSMENT_STATIC_ROOT / "css" / "assessment-v3.css").read_text(
            encoding="utf-8"
        )
        cls.behavior = (ASSESSMENT_STATIC_ROOT / "js" / "assessment-v3.js").read_text(
            encoding="utf-8"
        )

    def test_exam_mode_removes_hidden_mobile_navigation_inset(self):
        self.assertIn("body.exam-mode{padding-block-end:0}", self.styles)
        self.assertIn(".exam-mode #main{padding-block-end:0}", self.styles)

    def test_busy_submit_guard_blocks_duplicates_and_restores_bfcache_state(self):
        self.assertIn('form.dataset.submitState === "submitting"', self.behavior)
        self.assertIn("event.preventDefault();", self.behavior)
        self.assertIn("button.disabled = true;", self.behavior)
        self.assertIn("button.dataset.originalLabel", self.behavior)
        self.assertIn('window.addEventListener("pageshow"', self.behavior)
        self.assertIn('form.removeAttribute("data-submit-state")', self.behavior)

    def test_payment_consent_overrides_legacy_checkbox_layout(self):
        self.assertIn(
            ".manual-payment-form .consent-field{display:grid;grid-template-columns:minmax(0,1fr) auto",
            self.styles,
        )
        self.assertIn(
            '.manual-payment-form .consent-field input[type="checkbox"]',
            self.styles,
        )


class AssessmentAdminExportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="admin-export@example.com", email="=FORMULA@example.com", password="test",
            is_active=True,
        )
        self.exam = Exam.objects.create(
            slug="admin-export", title_fa="خروجی", title_en="Export",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
        )

    def test_order_csv_is_excel_compatible_selected_only_and_formula_safe(self):
        selected = Order.objects.create(
            user=self.user, exam=self.exam, subtotal_irr=500_000, discount_irr=500_000,
            discount_percent=100, amount_irr=0, gateway="free", status="paid",
        )
        other = Order.objects.create(
            user=self.user, exam=self.exam, subtotal_irr=500_000, amount_irr=500_000,
            gateway="sandbox", status="paid",
        )

        response = export_orders(None, None, Order.objects.filter(pk=selected.pk))
        content = response.content.decode("utf-8-sig")

        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("order_id,user_email,exam,subtotal_irr", content)
        self.assertIn("'=FORMULA@example.com", content)
        self.assertIn(str(selected.pk), content)
        self.assertNotIn(str(other.pk), content)
        self.assertIn(",100,500000,0,free,paid,", content)

    def test_operational_exports_omit_answers_and_ticket_messages(self):
        result_csv = export_results(None, None, AttemptResult.objects.none()).content.decode("utf-8-sig")
        ticket_csv = export_tickets(None, None, SupportTicket.objects.none()).content.decode("utf-8-sig")

        self.assertIn("score,level,correct,incorrect,unanswered,integrity", result_csv)
        self.assertNotIn("prompt", result_csv.lower())
        self.assertNotIn("selected_choice", result_csv.lower())
        self.assertNotIn("question", result_csv.lower())
        self.assertIn("ticket_id,user_email,category,status", ticket_csv)
        self.assertNotIn("message", ticket_csv.lower())

    def test_ticket_workflow_actions_do_not_reopen_closed_tickets(self):
        open_ticket = SupportTicket.objects.create(
            user=self.user, category="technical", subject="Open", message="Details",
        )
        closed_ticket = SupportTicket.objects.create(
            user=self.user, category="other", subject="Closed", message="Details", status="closed",
        )
        queryset = SupportTicket.objects.filter(pk__in=(open_ticket.pk, closed_ticket.pk))

        mark_tickets_in_review(None, None, queryset)
        open_ticket.refresh_from_db()
        closed_ticket.refresh_from_db()
        self.assertEqual(open_ticket.status, "in_review")
        self.assertEqual(closed_ticket.status, "closed")

        mark_tickets_resolved(None, None, queryset)
        open_ticket.refresh_from_db()
        closed_ticket.refresh_from_db()
        self.assertEqual(open_ticket.status, "resolved")
        self.assertEqual(closed_ticket.status, "closed")


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
        response = self.client.get("/fa/assessments/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "آزمون پایتون")

    def test_order_requires_login(self):
        response = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_legacy_get_purchase_link_returns_to_exam_without_creating_order(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:create_order", args=[self.exam.slug]))

        self.assertRedirects(
            response,
            reverse("assessments:detail", args=[self.exam.slug]) + "?lang=fa",
            fetch_redirect_response=False,
        )
        self.assertFalse(Order.objects.exists())

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_untouched_pending_order_refreshes_to_current_exam_price(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, subtotal_irr=500_000,
            amount_irr=500_000, gateway="card_transfer",
        )
        self.exam.price_irr = 1_200_000
        self.exam.save(update_fields=["price_irr"])
        self.client.force_login(self.user)

        response = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))

        self.assertRedirects(response, reverse("assessments:checkout", args=[order.pk]) + "?lang=fa")
        order.refresh_from_db()
        self.assertEqual(order.subtotal_irr, 1_200_000)
        self.assertEqual(order.amount_irr, 1_200_000)

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_pending_order_keeps_committed_price_after_terms_acceptance(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, subtotal_irr=500_000,
            amount_irr=500_000, gateway="card_transfer",
            terms_accepted_at=timezone.now(), terms_version="test-v1",
        )
        self.exam.price_irr = 1_200_000
        self.exam.save(update_fields=["price_irr"])
        self.client.force_login(self.user)

        self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))

        order.refresh_from_db()
        self.assertEqual(order.amount_irr, 500_000)

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_card_transfer_waits_for_admin_then_grants_access(self):
        self.client.force_login(self.user)
        self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))
        order = Order.objects.get()
        now = timezone.localtime()
        checkout = self.client.get(reverse("assessments:checkout", args=[order.pk]) + "?lang=fa")
        self.assertContains(checkout, 'class="jalali-date-select"', html=False)
        self.assertContains(checkout, "امروز —")
        self.assertNotContains(checkout, 'name="payment_date" type="date"', html=False)
        response = self.client.post(reverse("assessments:manual_payment_submit", args=[order.pk]) + "?lang=fa", {
            "payer_name": "خریدار آزمون", "reference_number": "۱۲۳۴۵۶۷۸",
            "payment_date": format_jalali(now.date()), "payment_time": now.strftime("%H:%M"),
            "note": "", "accept_terms": "on",
        })
        self.assertRedirects(response, reverse("assessments:checkout", args=[order.pk]) + "?lang=fa")
        submission = ManualPaymentSubmission.objects.get(order=order)
        self.assertEqual(submission.reference_number, "12345678")
        self.assertEqual(submission.status, "pending")
        self.assertFalse(ExamEntitlement.objects.filter(order=order).exists())
        admin_user = User.objects.create_superuser("owner@example.com", "owner@example.com", "secret")
        self.client.force_login(admin_user)
        self.client.post(reverse("admin:assessments_manualpaymentsubmission_changelist"), {
            "action": "approve_manual_payments", "_selected_action": [submission.pk],
        })
        submission.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(submission.status, "approved")
        self.assertEqual(order.status, "paid")
        self.assertEqual(ExamEntitlement.objects.filter(order=order).count(), 1)

        self.client.force_login(self.user)
        status = self.client.get(reverse("assessments:manual_payment_status", args=[order.pk]) + "?lang=fa")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["state"], "approved")
        self.assertTrue(status.json()["ready"])
        self.assertEqual(status.json()["redirect_url"], reverse("accounts:dashboard") + "?lang=fa")
        self.assertEqual(status["Cache-Control"], "no-store, private")

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_manual_payment_status_is_private_and_checkout_polls_for_approval(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, subtotal_irr=500_000,
            amount_irr=500_000, gateway="card_transfer",
        )
        ManualPaymentSubmission.objects.create(
            order=order, payer_name="Buyer", reference_number="12345678",
            paid_at=timezone.now(),
        )
        self.client.force_login(self.user)
        checkout = self.client.get(reverse("assessments:checkout", args=[order.pk]) + "?lang=fa")
        self.assertContains(checkout, "اطلاعات پرداخت را ثبت کن")
        self.assertNotContains(checkout, "آزمونت را رایگان فعال کن")
        self.assertContains(checkout, "اگر مدیر تا پایان شمارش اقدامی نکند")
        self.assertContains(checkout, reverse("assessments:manual_payment_status", args=[order.pk]))
        self.assertContains(checkout, "حداکثر زمان بررسی")
        self.assertContains(checkout, "data-payment-countdown")
        status = self.client.get(reverse("assessments:manual_payment_status", args=[order.pk]))
        self.assertEqual(status.json()["state"], "pending")
        self.assertFalse(status.json()["ready"])
        self.assertGreaterEqual(status.json()["auto_approve_seconds"], 0)
        self.assertLessEqual(status.json()["auto_approve_seconds"], 180)

        stranger = User.objects.create_user("stranger@example.com", password="test-password-42")
        self.client.force_login(stranger)
        forbidden = self.client.get(reverse("assessments:manual_payment_status", args=[order.pk]))
        self.assertEqual(forbidden.status_code, 404)

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_card_transfer_rejects_future_payment_time(self):
        order = Order.objects.create(user=self.user, exam=self.exam, subtotal_irr=500_000, amount_irr=500_000, gateway="card_transfer")
        self.client.force_login(self.user)
        future = timezone.localtime() + timedelta(days=1)
        response = self.client.post(reverse("assessments:manual_payment_submit", args=[order.pk]), {
            "payer_name": "Buyer", "reference_number": "987654", "payment_date": future.date(),
            "payment_time": future.strftime("%H:%M"), "accept_terms": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ManualPaymentSubmission.objects.exists())
        self.assertFalse(ExamEntitlement.objects.exists())

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_rejected_card_transfer_can_be_corrected_and_resubmitted(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, subtotal_irr=500_000,
            amount_irr=500_000, gateway="card_transfer",
        )
        reviewer = User.objects.create_superuser(
            username="payment-reviewer@example.com", email="payment-reviewer@example.com",
            password="safe-password",
        )
        submission = ManualPaymentSubmission.objects.create(
            order=order, payer_name="Old payer", reference_number="OLD1234",
            paid_at=timezone.now(), status="rejected", reviewed_by=reviewer,
            reviewed_at=timezone.now(), review_note="خوانا نیست",
        )
        self.client.force_login(self.user)
        now = timezone.localtime()

        response = self.client.post(
            reverse("assessments:manual_payment_submit", args=[order.pk]) + "?lang=fa",
            {
                "payer_name": "نام اصلاح‌شده", "reference_number": "NEW5678",
                "payment_date": format_jalali(now.date()),
                "payment_time": now.strftime("%H:%M"), "note": "رسید جدید",
                "accept_terms": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("assessments:checkout", args=[order.pk]) + "?lang=fa",
        )
        submission.refresh_from_db()
        self.assertEqual(submission.status, "pending")
        self.assertEqual(submission.reference_number, "NEW5678")
        self.assertIsNone(submission.reviewed_by)
        self.assertIsNone(submission.reviewed_at)
        self.assertEqual(submission.review_note, "")

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False, PAYMENT_GATEWAY="card_transfer")
    def test_rejected_card_transfer_checkout_offers_prefilled_recovery(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, subtotal_irr=500_000,
            amount_irr=500_000, gateway="card_transfer",
        )
        ManualPaymentSubmission.objects.create(
            order=order, payer_name="Previous payer", reference_number="OLD1234",
            paid_at=timezone.now(), status="rejected", review_note="تصویر رسید خوانا نیست",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("assessments:checkout", args=[order.pk]) + "?lang=fa",
        )

        self.assertContains(response, "اطلاعات قبلی تأیید نشد؛ قابل اصلاح است")
        self.assertContains(response, "تصویر رسید خوانا نیست")
        self.assertContains(response, "ارسال دوباره برای بررسی")
        self.assertContains(response, 'value="Previous payer"', html=False)
        self.assertNotContains(response, "data-payment-watch", html=False)

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False)
    def test_order_price_is_copied_from_exam_on_server(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]), {"amount_irr": 1})
        order = Order.objects.get()
        self.assertEqual(order.amount_irr, 500_000)
        self.assertRedirects(response, reverse("assessments:checkout", args=[order.pk]) + "?lang=fa")

    @override_settings(DEBUG=True, PAYMENT_GATEWAY="sandbox", ASSESSMENT_FREE_CHECKOUT=True)
    def test_local_free_checkout_records_full_discount_and_grants_access(self):
        self.client.force_login(self.user)
        created = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]) + "?lang=fa")
        order = Order.objects.get()

        self.assertEqual(order.subtotal_irr, 500_000)
        self.assertEqual(order.discount_irr, 500_000)
        self.assertEqual(order.discount_percent, 100)
        self.assertEqual(order.amount_irr, 0)
        self.assertEqual(order.gateway, "free")
        checkout = self.client.get(created.url)
        self.assertContains(checkout, "500,000")
        self.assertContains(checkout, "100٪")
        self.assertContains(checkout, "بدون اتصال به درگاه")

        confirmed = self.client.post(
            reverse("assessments:sandbox_pay", args=[order.pk]) + "?lang=fa",
            {"accept_terms": "yes"},
        )

        self.assertRedirects(confirmed, reverse("accounts:dashboard") + "?lang=fa")
        order.refresh_from_db()
        self.assertEqual(order.status, "paid")
        self.assertTrue(ExamEntitlement.objects.filter(order=order, attempts_remaining=1).exists())
        payment = PaymentTransaction.objects.get(order=order)
        self.assertEqual(payment.gateway, "free")
        self.assertEqual(payment.amount_irr, 0)

    def test_verified_payment_creates_exactly_one_entitlement(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=self.exam.price_irr,
            terms_version="test-v1", terms_accepted_at=timezone.now(),
        )
        first_order, created = verify_sandbox_payment(order.pk)
        second_order, created_again = verify_sandbox_payment(order.pk)
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first_order.status, "paid")
        self.assertEqual(second_order.status, "paid")
        self.assertEqual(ExamEntitlement.objects.count(), 1)
        self.assertEqual(PaymentTransaction.objects.filter(status="verified").count(), 1)

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False)
    def test_gateway_verification_rejects_wrong_amount_gateway_and_replay(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=self.exam.price_irr, gateway="provider",
            terms_version="test-v1", terms_accepted_at=timezone.now(),
        )
        for kwargs in (
            {"gateway": "other", "external_id": "ref-wrong-gateway", "amount_irr": 500_000},
            {"gateway": "provider", "external_id": "ref-wrong-amount", "amount_irr": 499_999},
        ):
            with self.assertRaises(PaymentVerificationError):
                verify_gateway_payment(order.pk, **kwargs)
        order.refresh_from_db()
        self.assertEqual(order.status, "pending")
        self.assertFalse(PaymentTransaction.objects.exists())

        verify_gateway_payment(
            order.pk, gateway="provider", external_id="provider-ref-1", amount_irr=500_000,
        )
        second_order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=500_000, gateway="provider",
            terms_version="test-v1", terms_accepted_at=timezone.now(), status="cancelled",
        )
        second_order.status = "pending"
        second_order.save(update_fields=["status"])
        with self.assertRaises(PaymentVerificationError):
            verify_gateway_payment(
                second_order.pk, gateway="provider", external_id="provider-ref-1", amount_irr=500_000,
            )
        self.assertEqual(ExamEntitlement.objects.count(), 1)

    @override_settings(ASSESSMENT_FREE_CHECKOUT=False)
    def test_gateway_response_is_sanitized_and_callback_is_idempotent(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=500_000, gateway="provider",
            terms_version="test-v1", terms_accepted_at=timezone.now(),
        )
        first, created = verify_gateway_payment(
            order.pk, gateway="provider", external_id="provider-ref-safe", amount_irr=500_000,
            response={"status_code": 100, "tracking": "ok", "token": "secret-value", "nested": {"private": True}},
        )
        second, created_again = verify_gateway_payment(
            order.pk, gateway="provider", external_id="provider-ref-safe", amount_irr=500_000,
        )
        payment = PaymentTransaction.objects.get(external_id="provider-ref-safe")

        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(payment.raw_response, {"status_code": 100, "tracking": "ok", "verified": True})
        self.assertEqual(ExamEntitlement.objects.filter(order=order).count(), 1)

    @override_settings(DEBUG=True, PAYMENT_GATEWAY="sandbox")
    def test_payment_requires_server_recorded_terms_acceptance(self):
        order = Order.objects.create(user=self.user, exam=self.exam, amount_irr=self.exam.price_irr)
        with self.assertRaises(PaymentVerificationError):
            verify_sandbox_payment(order.pk)
        self.client.force_login(self.user)
        url = reverse("assessments:sandbox_pay", args=[order.pk]) + "?lang=en"

        rejected = self.client.post(url)

        order.refresh_from_db()
        self.assertRedirects(rejected, reverse("assessments:checkout", args=[order.pk]) + "?lang=en")
        self.assertEqual(order.status, "pending")
        self.assertIsNone(order.terms_accepted_at)
        self.assertFalse(ExamEntitlement.objects.filter(order=order).exists())

        accepted = self.client.post(url, {"accept_terms": "yes"})

        order.refresh_from_db()
        self.assertRedirects(accepted, reverse("accounts:dashboard") + "?lang=en")
        self.assertEqual(order.status, "paid")
        self.assertTrue(order.terms_version)
        self.assertIsNotNone(order.terms_accepted_at)
        self.assertTrue(ExamEntitlement.objects.filter(order=order).exists())

    @override_settings(DEBUG=True, PAYMENT_GATEWAY="sandbox")
    def test_payment_confirmation_email_is_bilingual_and_not_duplicated(self):
        order = Order.objects.create(user=self.user, exam=self.exam, amount_irr=self.exam.price_irr)
        self.client.force_login(self.user)
        url = reverse("assessments:sandbox_pay", args=[order.pk]) + "?lang=en"

        first = self.client.post(url, {"accept_terms": "yes"})
        second = self.client.post(url, {"accept_terms": "yes"})

        self.assertRedirects(first, reverse("accounts:dashboard") + "?lang=en")
        self.assertRedirects(second, reverse("accounts:dashboard") + "?lang=en")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("payment is confirmed", mail.outbox[0].subject)
        self.assertIn(str(order.pk), mail.outbox[0].body)
        self.assertIn(f"/en/account/orders/{order.pk}/receipt/", mail.outbox[0].body)
        self.assertNotIn("?lang=", mail.outbox[0].body)
        order.refresh_from_db()
        self.assertIsNotNone(order.confirmation_email_sent_at)

    @override_settings(DEBUG=True, PAYMENT_GATEWAY="sandbox")
    @patch("assessments.emails.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_email_failure_does_not_rollback_verified_payment(self, mocked_send):
        order = Order.objects.create(user=self.user, exam=self.exam, amount_irr=self.exam.price_irr)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("assessments:sandbox_pay", args=[order.pk]) + "?lang=fa",
            {"accept_terms": "yes"},
        )

        self.assertRedirects(response, reverse("accounts:dashboard") + "?lang=fa")
        order.refresh_from_db()
        self.assertEqual(order.status, "paid")
        self.assertIsNone(order.confirmation_email_sent_at)
        self.assertTrue(ExamEntitlement.objects.filter(order=order).exists())
        mocked_send.assert_called_once()

    def test_assessment_terms_are_public_and_bilingual(self):
        english = self.client.get(reverse("assessments:terms") + "?lang=en")
        persian = self.client.get(reverse("assessments:terms") + "?lang=fa")
        self.assertContains(english, "not official, academic")
        self.assertContains(english, "AI-assisted")
        self.assertContains(persian, "رسمی، دانشگاهی")

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

    def test_pending_order_is_reused_instead_of_creating_duplicates(self):
        self.client.force_login(self.user)
        pending = Order.objects.create(user=self.user, exam=self.exam, amount_irr=self.exam.price_irr)
        first = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))
        second = self.client.post(reverse("assessments:create_order", args=[self.exam.slug]))
        expected = reverse("assessments:checkout", args=[pending.pk]) + "?lang=fa"
        self.assertRedirects(first, expected)
        self.assertRedirects(second, expected)
        self.assertEqual(Order.objects.count(), 1)

    def test_support_requires_login(self):
        response = self.client.get(reverse("assessments:support_create"))
        self.assertIn(reverse("accounts:login"), response.url)

    def test_support_ticket_accepts_owned_order_and_notifies_staff(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=self.exam.price_irr, status="paid",
        )
        self.client.force_login(self.user)

        response = self.client.post(reverse("assessments:support_create") + "?lang=en", {
            "category": "payment", "order": order.pk, "result": "",
            "subject": "Payment receipt question", "message": "Please review this payment record in detail.",
            "website": "",
        })

        self.assertRedirects(response, reverse("assessments:support_history") + "?lang=en")
        ticket = SupportTicket.objects.get()
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.order, order)
        self.assertEqual(ticket.status, "open")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"Support #{ticket.pk}", mail.outbox[0].subject)

    def test_support_rejects_foreign_reference_and_honeypot(self):
        other = User.objects.create_user(
            username="ticket-other@example.com", email="ticket-other@example.com",
            password="test", is_active=True,
        )
        foreign_order = Order.objects.create(
            user=other, exam=self.exam, amount_irr=self.exam.price_irr, status="paid",
        )
        self.client.force_login(self.user)
        url = reverse("assessments:support_create") + "?lang=en"
        payload = {
            "category": "payment", "order": foreign_order.pk, "result": "",
            "subject": "Foreign reference", "message": "This should never be attached to another user.",
            "website": "",
        }

        foreign = self.client.post(url, payload)
        payload.update({"order": "", "website": "https://spam.example"})
        spam = self.client.post(url, payload)

        self.assertEqual(foreign.status_code, 200)
        self.assertEqual(spam.status_code, 200)
        self.assertEqual(SupportTicket.objects.count(), 0)

    def test_support_history_is_private(self):
        other = User.objects.create_user(
            username="private-ticket@example.com", email="private-ticket@example.com",
            password="test", is_active=True,
        )
        SupportTicket.objects.create(
            user=self.user, category="technical", subject="Owner ticket", message="Owner details",
        )
        SupportTicket.objects.create(
            user=other, category="technical", subject="Private stranger ticket", message="Private details",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:support_history") + "?lang=en")

        self.assertContains(response, "Owner ticket")
        self.assertNotContains(response, "Private stranger ticket")

    @override_settings(ASSESSMENT_SUPPORT_TICKETS_PER_HOUR=2)
    def test_authenticated_support_spam_is_hourly_limited(self):
        SupportTicket.objects.bulk_create([
            SupportTicket(
                user=self.user, category="technical", subject=f"Existing {index}",
                message="A previously submitted support request.",
            )
            for index in range(2)
        ])
        self.client.force_login(self.user)

        response = self.client.post(reverse("assessments:support_create") + "?lang=en", {
            "category": "technical", "order": "", "result": "",
            "subject": "Too many requests", "message": "This request must be throttled safely.",
            "website": "",
        })

        self.assertRedirects(response, reverse("assessments:support_history") + "?lang=en")
        self.assertEqual(SupportTicket.objects.count(), 2)
        self.assertEqual(len(mail.outbox), 0)


class AssessmentEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="candidate@example.com", email="candidate@example.com",
            password="test-password-42", is_active=True, email_verified=True,
            first_name="Candidate", last_name="Example",
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
            explanation_fa="دلیل علمی پاسخ.", explanation_en="Scientific answer rationale.",
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
        self.assertEqual(len(attempt.selection_seed), 64)
        self.assertEqual(attempt.attempt_questions.count(), 2)
        self.assertEqual(len(set(attempt.attempt_questions.values_list("question_id", flat=True))), 2)
        self.assertTrue(all(len(row.choice_order) == 4 for row in attempt.attempt_questions.all()))
        self.assertTrue(all(row.question_snapshot for row in attempt.attempt_questions.all()))
        self.assertTrue(all(len(row.choices_snapshot) == 4 for row in attempt.attempt_questions.all()))
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 0)

    def test_selection_prefers_questions_not_seen_in_recent_attempts(self):
        first_attempt = self.start()
        first_ids = set(first_attempt.attempt_questions.values_list("question_id", flat=True))
        unseen_id = next(question.pk for question in self.questions if question.pk not in first_ids)
        second_order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=self.exam.price_irr, status="paid",
        )
        second_entitlement = ExamEntitlement.objects.create(
            user=self.user, exam=self.exam, order=second_order, attempts_remaining=1,
        )
        second_attempt, _ = start_attempt(second_entitlement.pk, self.user)
        second_ids = set(second_attempt.attempt_questions.values_list("question_id", flat=True))
        self.assertIn(unseen_id, second_ids)

    def test_blueprint_is_deterministic_and_respects_difficulty_and_content_groups(self):
        pool = [
            (1, 1, "foundation-a"), (2, 1, "foundation-b"),
            (3, 3, "intermediate-a"), (4, 3, "intermediate-b"),
            (5, 5, "expert-a"), (6, 5, "expert-b"),
        ]
        blueprint = {"1": 1, "3": 1, "5": 1}
        first = _choose_section_questions(pool, 3, random.Random("audit-seed"), {1}, blueprint)
        second = _choose_section_questions(pool, 3, random.Random("audit-seed"), {1}, blueprint)
        self.assertEqual(first, second)
        selected_difficulties = sorted(item[1] for item in pool if item[0] in first)
        self.assertEqual(selected_difficulties, [1, 3, 5])
        self.assertNotIn(1, first)

    def test_one_thousand_generated_forms_remain_balanced_and_diverse(self):
        pool = [
            (question_id, ((question_id - 1) // 40) + 1, f"concept-{question_id}")
            for question_id in range(1, 201)
        ]
        blueprint = {str(level): 10 for level in range(1, 6)}
        recent_ids = {
            question_id
            for level in range(5)
            for question_id in range(level * 40 + 1, level * 40 + 6)
        }
        forms = set()
        for index in range(1000):
            selected = _choose_section_questions(
                pool, 50, random.Random(f"audit-{index}"), recent_ids, blueprint,
            )
            self.assertEqual(len(selected), 50)
            self.assertTrue(recent_ids.isdisjoint(selected))
            difficulties = [item[1] for item in pool if item[0] in selected]
            self.assertEqual({level: difficulties.count(level) for level in range(1, 6)}, {
                level: 10 for level in range(1, 6)
            })
            forms.add(tuple(selected))
        self.assertEqual(len(forms), 1000)

    def test_snapshot_keeps_scoring_stable_after_question_bank_changes(self):
        attempt = self.start()
        row = attempt.attempt_questions.first()
        original_correct = row.question.choices.get(is_correct=True)
        replacement = row.question.choices.filter(is_correct=False).first()
        row.selected_choice = original_correct
        row.save(update_fields=["selected_choice"])
        original_correct.is_correct = False
        original_correct.save(update_fields=["is_correct"])
        replacement.is_correct = True
        replacement.save(update_fields=["is_correct"])
        row.question.weight = 5
        row.question.save(update_fields=["weight"])
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)
        self.assertEqual(result.correct_count, 1)
        self.assertEqual(result.percentage, 50)

    def test_result_ready_email_contains_private_report_and_certificate_once(self):
        attempt = self.start()
        attempt.status = "submitted"
        attempt.completion_reason = "manual"
        attempt.save(update_fields=["status", "completion_reason"])
        result, _ = score_attempt(attempt.pk)
        self.client.force_login(self.user)
        url = reverse("assessments:result", args=[result.pk]) + "?lang=en"

        first = self.client.get(url)
        second = self.client.get(url)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("result is ready", mail.outbox[0].subject)
        self.assertIn(f"/en/assessments/result/{result.pk}/", mail.outbox[0].body)
        self.assertNotIn("?lang=", mail.outbox[0].body)
        self.assertIn(
            f"/en/assessments/certificate/{result.certificate.verification_code}/",
            mail.outbox[0].body,
        )
        self.assertIn("not official or academic", mail.outbox[0].body)
        result.refresh_from_db()
        self.assertIsNotNone(result.report_email_sent_at)
        self.assertContains(second, "Report and certificate links were emailed")

    @patch("assessments.emails.send_mail", side_effect=RuntimeError("SMTP unavailable"))
    def test_result_page_survives_email_failure_and_can_retry(self, mocked_send):
        attempt = self.start()
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:result", args=[result.pk]) + "?lang=fa")

        self.assertEqual(response.status_code, 200)
        result.refresh_from_db()
        self.assertIsNone(result.report_email_sent_at)
        mocked_send.assert_called_once()

    def test_start_attempt_has_bounded_query_count(self):
        with CaptureQueriesContext(connection) as queries:
            start_attempt(self.entitlement.pk, self.user)
        # The user-row lock and rolling-window count make the daily limit safe
        # across concurrent starts while keeping the workflow bounded.
        self.assertLessEqual(len(queries), 16)

    def test_start_is_idempotent(self):
        first, _ = start_attempt(self.entitlement.pk, self.user)
        second, created = start_attempt(self.entitlement.pk, self.user)
        self.assertFalse(created)
        self.assertEqual(first.pk, second.pk)
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 0)

    def test_daily_limit_counts_started_attempts_and_preserves_paid_entitlement(self):
        now = timezone.now()
        for index in range(5):
            order = Order.objects.create(
                user=self.user, exam=self.exam, amount_irr=self.exam.price_irr, status="paid",
            )
            entitlement = ExamEntitlement.objects.create(
                user=self.user, exam=self.exam, order=order, attempts_remaining=0,
            )
            Attempt.objects.create(
                user=self.user, exam=self.exam, version=self.version, entitlement=entitlement,
                status="completed", started_at=now - timedelta(hours=index),
                expires_at=now + timedelta(minutes=10),
            )

        with self.assertRaises(AttemptLimitError):
            self.start()

        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 1)
        self.assertFalse(Attempt.objects.filter(entitlement=self.entitlement).exists())

    def test_attempt_older_than_24_hours_does_not_consume_daily_limit(self):
        order = Order.objects.create(
            user=self.user, exam=self.exam, amount_irr=self.exam.price_irr, status="paid",
        )
        old_entitlement = ExamEntitlement.objects.create(
            user=self.user, exam=self.exam, order=order, attempts_remaining=0,
        )
        Attempt.objects.create(
            user=self.user, exam=self.exam, version=self.version, entitlement=old_entitlement,
            status="completed", started_at=timezone.now() - timedelta(hours=25),
            expires_at=timezone.now() - timedelta(hours=24),
        )

        attempt = self.start()

        self.assertEqual(attempt.entitlement, self.entitlement)

    def test_expired_entitlement_cannot_start_and_is_not_consumed(self):
        self.entitlement.expires_at = timezone.now() - timedelta(seconds=1)
        self.entitlement.save(update_fields=["expires_at"])

        with self.assertRaisesMessage(ExamContentError, "entitlement has expired"):
            self.start()

        self.assertFalse(Attempt.objects.filter(entitlement=self.entitlement).exists())
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 1)

    def test_start_view_requires_complete_certificate_identity(self):
        self.user.last_name = ""
        self.user.save(update_fields=["last_name"])
        self.client.force_login(self.user)

        response = self.client.post(reverse("assessments:start_attempt", args=[self.entitlement.pk]) + "?lang=en")

        self.assertRedirects(response, reverse("accounts:profile_identity") + "?lang=en")
        self.assertFalse(Attempt.objects.exists())
        self.entitlement.refresh_from_db()
        self.assertEqual(self.entitlement.attempts_remaining, 1)

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
        self.assertEqual(self.client.get(reverse("assessments:attempt_review", args=[attempt.pk])).status_code, 404)

    def test_attempt_and_review_keep_a_single_main_landmark(self):
        attempt = self.start()
        self.client.force_login(self.user)

        attempt_response = self.client.get(
            reverse("assessments:attempt", args=[attempt.pk]) + "?lang=fa"
        )
        review_response = self.client.get(
            reverse("assessments:attempt_review", args=[attempt.pk]) + "?lang=fa"
        )
        attempt_html = attempt_response.content.decode()
        review_html = review_response.content.decode()

        self.assertEqual(attempt_html.count("<main"), 1)
        self.assertEqual(review_html.count("<main"), 1)
        self.assertIn(
            '<section class="question-stage" aria-labelledby="assessment-question-title">',
            attempt_html,
        )
        self.assertIn(
            '<section class="attempt-review" aria-labelledby="attempt-review-title">',
            review_html,
        )
        self.assertIn('data-busy-label="در حال ثبت نهایی…"', review_html)

    def test_deleted_live_choice_remains_answerable_and_scores_from_snapshot(self):
        Question.objects.filter(pk__in=[question.pk for question in self.questions]).update(
            question_type="listening",
            audio_path="assessments/audio/clip01.wav",
            max_plays=2,
        )
        attempt = self.start()
        row = attempt.attempt_questions.first()
        snapshot_prompt = row.question_snapshot["prompt_en"]
        snapshot_choices = {choice["id"]: choice["text_en"] for choice in row.choices_snapshot}
        deleted_choice_id = next(
            choice["id"] for choice in row.choices_snapshot if choice["is_correct"]
        )
        deleted_choice_text = snapshot_choices[deleted_choice_id]

        row.question.prompt_en = "MUTATED LIVE QUESTION"
        row.question.audio_path = "assessments/audio/mutated.wav"
        row.question.max_plays = 0
        row.question.save(update_fields=["prompt_en", "audio_path", "max_plays"])
        remaining_choice = row.question.choices.exclude(pk=deleted_choice_id).first()
        remaining_choice.text_en = "MUTATED LIVE CHOICE"
        remaining_choice.save(update_fields=["text_en"])
        row.question.choices.get(pk=deleted_choice_id).delete()
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("assessments:attempt", args=[attempt.pk]) + f"?q={row.position}&lang=en"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, snapshot_prompt)
        self.assertContains(response, deleted_choice_text)
        self.assertContains(response, "assessments/audio/clip01.wav")
        self.assertNotContains(response, "MUTATED LIVE QUESTION")
        self.assertNotContains(response, "MUTATED LIVE CHOICE")
        self.assertNotContains(response, "assessments/audio/mutated.wav")
        audio_response = self.client.post(
            reverse("assessments:audio_play", args=[attempt.pk, row.pk])
        )
        self.assertEqual(audio_response.status_code, 200)
        self.assertEqual(audio_response.json()["remaining"], 1)
        save_response = self.client.post(
            reverse("assessments:save_answer", args=[attempt.pk, row.pk]),
            {"choice": deleted_choice_id},
        )
        self.assertEqual(save_response.status_code, 200)
        self.assertEqual(save_response.json()["answered"], 1)
        row.refresh_from_db()
        self.assertEqual(row.selected_choice_snapshot_id, deleted_choice_id)
        self.assertIsNone(row.selected_choice_id)

        review = self.client.get(
            reverse("assessments:attempt_review", args=[attempt.pk]) + "?lang=en"
        )
        self.assertEqual(review.context["answered_count"], 1)
        finish = self.client.post(
            reverse("assessments:finish_attempt", args=[attempt.pk]) + "?lang=en",
            {"confirm_submission": "yes"},
        )
        result = AttemptResult.objects.get(attempt=attempt)
        self.assertRedirects(
            finish,
            reverse("assessments:result", args=[result.pk]) + "?lang=en",
        )
        self.assertEqual(result.correct_count, 1)
        self.assertEqual(result.incorrect_count, 0)
        self.assertEqual(result.unanswered_count, 1)
        self.assertEqual(result.percentage, 50)
        result_page = self.client.get(
            reverse("assessments:result", args=[result.pk]) + "?lang=en"
        )
        self.assertContains(result_page, deleted_choice_text)

    def test_attempt_review_shows_answered_and_unanswered_questions(self):
        attempt = self.start()
        first = attempt.attempt_questions.first()
        first.selected_choice = first.question.choices.first()
        first.save(update_fields=["selected_choice"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:attempt_review", args=[attempt.pk]) + "?lang=en")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["answered_count"], 1)
        self.assertEqual(response.context["unanswered_count"], 1)
        self.assertContains(response, "1 questions are still unanswered")
        self.assertContains(response, "Submission cannot be undone")
        self.assertContains(response, f"q={first.position}")

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

    def test_question_telemetry_counts_visits_time_and_answer_changes(self):
        attempt = self.start()
        item = attempt.attempt_questions.first()
        choices = list(item.question.choices.order_by("display_order")[:2])
        self.client.force_login(self.user)

        page = self.client.get(reverse("assessments:attempt", args=[attempt.pk]) + f"?q={item.position}")
        self.assertEqual(page.status_code, 200)
        first = self.client.post(
            reverse("assessments:save_answer", args=[attempt.pk, item.pk]),
            {"choice": choices[0].pk, "active_seconds": "17"},
        )
        second = self.client.post(
            reverse("assessments:save_answer", args=[attempt.pk, item.pk]),
            {"choice": choices[1].pk, "active_seconds": "9999"},
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        item.refresh_from_db()
        self.assertIsNotNone(item.first_seen_at)
        self.assertEqual(item.visit_count, 1)
        self.assertEqual(item.active_seconds, 917)
        self.assertEqual(item.answer_change_count, 1)

    def test_attempt_navigation_waits_for_pending_answer_and_has_timeout_recovery(self):
        attempt = self.start()
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:attempt", args=[attempt.pk]) + "?q=1&lang=fa")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-exam-nav")
        self.assertContains(response, "data-question-nav")
        self.assertContains(response, "const flushSave=")
        self.assertContains(response, "AbortController")
        self.assertContains(response, "15000")
        self.assertContains(response, "location.replace(link.href)")
        self.assertContains(response, "else location.assign(link.href)")
        self.assertContains(response, "internalNavigation=true")
        self.assertContains(response, "if(internalNavigation)return")
        self.assertContains(response, "visibility_hidden")
        self.assertContains(response, "visibility_returned")
        self.assertContains(response, "پاسخ ذخیره نشد؛ اتصال را بررسی")

    def test_reload_without_query_resumes_the_last_server_recorded_question(self):
        attempt = self.start()
        self.client.force_login(self.user)
        url = reverse("assessments:attempt", args=[attempt.pk])

        moved = self.client.get(url + "?q=2&lang=fa")
        resumed = self.client.get(url + "?lang=fa")

        self.assertEqual(moved.context["position"], 2)
        self.assertEqual(resumed.context["position"], 2)
        attempt.refresh_from_db()
        self.assertEqual(attempt.current_position, 2)

    def test_listening_play_count_is_limited_to_two(self):
        Question.objects.filter(pk__in=[question.pk for question in self.questions]).update(
            question_type="listening", audio_path="assessments/audio/clip01.wav",
            transcript="Test transcript", max_plays=2,
        )
        attempt = self.start()
        item = attempt.attempt_questions.first()
        self.client.force_login(self.user)
        url = reverse("assessments:audio_play", args=[attempt.pk, item.pk])
        self.assertEqual(self.client.post(url).status_code, 200)
        second = self.client.post(url)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["remaining"], 0)
        third = self.client.post(url)
        self.assertEqual(third.status_code, 429)
        item.refresh_from_db()
        self.assertEqual(item.audio_play_count, 2)

    def test_visibility_absence_is_paired_and_scored_by_server_duration(self):
        attempt = self.start()
        item = attempt.attempt_questions.first()
        self.client.force_login(self.user)
        url = reverse("assessments:integrity_event", args=[attempt.pk])
        hidden = self.client.post(url, {"event_type": "visibility_hidden", "item_id": item.pk})
        event = IntegrityEvent.objects.get(attempt=attempt, event_type="visibility_hidden")
        IntegrityEvent.objects.filter(pk=event.pk).update(created_at=timezone.now() - timedelta(seconds=20))
        returned = self.client.post(url, {
            "event_type": "visibility_returned", "item_id": item.pk, "duration_ms": "1",
        })
        self.assertEqual(hidden.status_code, 200)
        self.assertEqual(returned.status_code, 200)
        self.assertEqual(returned.json()["risk_points"], 3)
        attempt.refresh_from_db()
        self.assertEqual(attempt.integrity_score, 97)
        return_event = IntegrityEvent.objects.get(attempt=attempt, event_type="visibility_returned")
        self.assertGreaterEqual(return_event.duration_ms, 19_000)
        self.assertEqual(return_event.attempt_question, item)

    def test_visibility_return_without_recorded_exit_is_rejected(self):
        attempt = self.start()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("assessments:integrity_event", args=[attempt.pk]),
            {"event_type": "visibility_returned", "duration_ms": "60000"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["reason"], "missing_hidden_event")
        attempt.refresh_from_db()
        self.assertEqual(attempt.integrity_score, 100)

    def test_micro_visibility_absence_is_recorded_without_penalty(self):
        attempt = self.start()
        self.client.force_login(self.user)
        url = reverse("assessments:integrity_event", args=[attempt.pk])
        self.client.post(url, {"event_type": "visibility_hidden"})
        hidden = IntegrityEvent.objects.get(attempt=attempt, event_type="visibility_hidden")
        IntegrityEvent.objects.filter(pk=hidden.pk).update(
            created_at=timezone.now() - timedelta(seconds=1)
        )
        returned = self.client.post(url, {"event_type": "visibility_returned"})
        attempt.refresh_from_db()
        self.assertEqual(returned.json()["risk_points"], 0)
        self.assertEqual(attempt.integrity_score, 100)

    def test_legacy_navigation_events_are_not_treated_as_reliable_evidence(self):
        legacy = assess_event("tab_hidden", 60_000)

        self.assertEqual(legacy.points, 0)
        self.assertEqual(legacy.severity, "info")
        self.assertIn("غیرقابل اتکا", legacy.reason_fa)

    def test_integrity_event_is_scoped_to_question_and_rejects_foreign_item(self):
        attempt = self.start()
        item = attempt.attempt_questions.first()
        other_user = User.objects.create_user(username="other@example.com", password="test-password")
        other_order = Order.objects.create(user=other_user, exam=self.exam, amount_irr=0, status="paid")
        other_entitlement = ExamEntitlement.objects.create(user=other_user, exam=self.exam, order=other_order)
        other_attempt = Attempt.objects.create(
            user=other_user, exam=self.exam, version=self.version, entitlement=other_entitlement,
            status="in_progress", started_at=timezone.now(), expires_at=timezone.now() + timedelta(minutes=10),
        )
        foreign_item = AttemptQuestion.objects.create(
            attempt=other_attempt, question=self.questions[-1], position=1,
            choice_order=[], question_snapshot={}, choices_snapshot=[],
        )
        self.client.force_login(self.user)
        url = reverse("assessments:integrity_event", args=[attempt.pk])

        accepted = self.client.post(url, {
            "event_type": "copy", "item_id": item.pk, "duration_ms": "9999999",
        })
        rejected = self.client.post(url, {"event_type": "paste", "item_id": foreign_item.pk})

        self.assertEqual(accepted.status_code, 200)
        event = IntegrityEvent.objects.get(attempt=attempt, event_type="copy")
        self.assertEqual(event.attempt_question, item)
        self.assertEqual(event.duration_ms, 900_000)
        self.assertEqual(rejected.status_code, 404)

    def test_integrity_copy_events_are_deduplicated_per_question(self):
        attempt = self.start()
        item = attempt.attempt_questions.first()
        self.client.force_login(self.user)
        url = reverse("assessments:integrity_event", args=[attempt.pk])
        first = self.client.post(url, {"event_type": "copy", "item_id": item.pk})
        duplicate = self.client.post(url, {"event_type": "copy", "item_id": item.pk})
        self.assertEqual(first.status_code, 200)
        self.assertTrue(duplicate.json()["deduplicated"])
        self.assertEqual(IntegrityEvent.objects.filter(attempt=attempt).count(), 1)
        attempt.refresh_from_db()
        self.assertEqual(attempt.integrity_score, 98)

    def test_finish_submits_attempt(self):
        attempt = self.start()
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("assessments:finish_attempt", args=[attempt.pk]),
            {"confirm_submission": "yes"},
        )
        result = AttemptResult.objects.get(attempt=attempt)
        self.assertRedirects(response, reverse("assessments:result", args=[result.pk]) + "?lang=fa")
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "completed")
        self.assertEqual(attempt.completion_reason, "manual")
        self.assertTrue(Certificate.objects.filter(result=result).exists())

    def test_finish_requires_named_confirmation_on_server(self):
        attempt = self.start()
        self.client.force_login(self.user)
        review_url = reverse("assessments:attempt_review", args=[attempt.pk]) + "?lang=en"

        review = self.client.get(review_url)
        invalid = self.client.post(
            reverse("assessments:finish_attempt", args=[attempt.pk]) + "?lang=en",
            {},
            follow=True,
        )

        self.assertContains(review, 'name="confirm_submission"')
        self.assertContains(review, 'value="yes"')
        self.assertContains(invalid, "Confirm that you are ready before submitting")
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "in_progress")
        self.assertFalse(AttemptResult.objects.filter(attempt=attempt).exists())

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
        self.assertTrue(response.json()["result_url"])
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, "completed")
        self.assertEqual(attempt.completion_reason, "timeout")
        self.assertTrue(AttemptResult.objects.filter(attempt=attempt).exists())

    def test_timeout_is_scored_once_and_attempt_page_redirects_to_result(self):
        attempt = self.start()
        first = attempt.attempt_questions.first()
        first.selected_choice = first.question.choices.get(is_correct=True)
        first.save(update_fields=["selected_choice"])
        attempt.expires_at = timezone.now()
        attempt.save(update_fields=["expires_at"])

        first_result = finalize_expired_attempt(attempt.pk)
        second_result = finalize_expired_attempt(attempt.pk)

        self.assertEqual(first_result.pk, second_result.pk)
        self.assertEqual(AttemptResult.objects.filter(attempt=attempt).count(), 1)
        self.assertEqual(first_result.correct_count, 1)
        self.assertEqual(first_result.unanswered_count, 1)
        self.client.force_login(self.user)
        response = self.client.get(attempt.get_absolute_url() + "?lang=en")
        self.assertRedirects(
            response, reverse("assessments:result", args=[first_result.pk]) + "?lang=en"
        )
        report = self.client.get(reverse("assessments:result", args=[first_result.pk]) + "?lang=en")
        self.assertContains(report, "Assessment time expired")
        self.assertContains(report, "saved answers were submitted and scored automatically")

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

    def test_certificate_holder_name_is_frozen_at_issue_time(self):
        attempt = self.start()
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)
        self.assertEqual(result.certificate.holder_name, "Candidate Example")
        self.user.first_name = "Changed"
        self.user.last_name = "Later"
        self.user.save(update_fields=["first_name", "last_name"])

        response = self.client.get(
            reverse("assessments:certificate", args=[result.certificate.verification_code]) + "?lang=en"
        )

        self.assertContains(response, "Candidate Example")
        self.assertNotContains(response, "Changed Later")

    def test_result_is_private_but_certificate_is_verifiable(self):
        attempt = self.start()
        attempt.status = "submitted"
        attempt.save()
        result, _ = score_attempt(attempt.pk)
        other = User.objects.create_user(username="viewer@example.com", email="viewer@example.com", password="test")
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse("assessments:result", args=[result.pk])).status_code, 404)
        certificate_response = self.client.get(
            reverse("assessments:certificate", args=[result.certificate.verification_code]) + "?lang=en"
        )
        self.assertEqual(certificate_response.status_code, 200)
        self.assertContains(certificate_response, result.certificate.verification_code)
        self.assertContains(certificate_response, "RESULT IS VERIFIABLE")
        self.assertContains(certificate_response, "Integrity")
        self.assertContains(certificate_response, f"Assessment version {attempt.version.version}")
        self.assertNotContains(certificate_response, self.user.email)

    def test_integrity_summary_counts_events_and_flags_low_score(self):
        attempt = self.start()
        attempt.integrity_score = 72
        attempt.status = "submitted"
        attempt.save(update_fields=["integrity_score", "status"])
        IntegrityEvent.objects.create(attempt=attempt, event_type="tab_hidden")
        IntegrityEvent.objects.create(attempt=attempt, event_type="tab_hidden")
        IntegrityEvent.objects.create(attempt=attempt, event_type="copy")
        result, _ = score_attempt(attempt.pk)
        self.client.force_login(self.user)

        report = self.client.get(reverse("assessments:result", args=[result.pk]) + "?lang=en")
        certificate = self.client.get(
            reverse("assessments:certificate", args=[result.certificate.verification_code]) + "?lang=en"
        )

        self.assertContains(report, "Review by receiving organization")
        self.assertContains(report, "Legacy unreliable event")
        self.assertContains(report, "Copy attempts")
        self.assertContains(certificate, "MANUAL REVIEW REQUIRED")
        self.assertContains(certificate, "72%")

    def test_public_verifier_accepts_formatted_persian_digit_code_without_private_email(self):
        attempt = self.start()
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)
        code = result.certificate.verification_code
        persian_digits = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
        formatted_code = f"{code[:4]}-{code[4:8]} {code[8:]}".translate(persian_digits)

        response = self.client.get(
            reverse("assessments:verify_certificate"), {"lang": "en", "code": formatted_code}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certificate is valid and active")
        self.assertContains(response, code)
        self.assertNotContains(response, self.user.email)

    def test_public_verifier_rejects_unknown_and_revoked_certificates(self):
        unknown = self.client.get(
            reverse("assessments:verify_certificate"), {"lang": "en", "code": "FFFFFFFFFFFF"}
        )
        self.assertContains(unknown, "No valid certificate was found")
        attempt = self.start()
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)
        result.certificate.is_revoked = True
        result.certificate.save(update_fields=["is_revoked"])

        revoked = self.client.get(
            reverse("assessments:verify_certificate"),
            {"lang": "en", "code": result.certificate.verification_code},
        )

        self.assertContains(revoked, "This certificate has been revoked")
        self.assertNotContains(revoked, self.exam.title_en)

    def test_result_reviews_correct_incorrect_and_unanswered_answers(self):
        attempt = self.start()
        rows = list(attempt.attempt_questions.select_related("question"))
        correct_choice = rows[0].question.choices.get(is_correct=True)
        rows[0].selected_choice = correct_choice
        rows[0].save(update_fields=["selected_choice"])
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:result", args=[result.pk]) + "?lang=en")

        self.assertContains(response, "Complete answer review")
        self.assertContains(response, "Your answer")
        self.assertContains(response, correct_choice.text_en)
        self.assertContains(response, "No answer was submitted.")
        self.assertContains(response, "Why is this answer appropriate?")
        self.assertContains(response, "Why is this the correct answer?")
        self.assertContains(response, "Suggested learning plan")
        self.assertEqual(sum(len(items) for _, items in response.context["review_groups"]), 2)

    def test_result_review_uses_immutable_snapshot_after_bank_changes(self):
        attempt = self.start()
        row = attempt.attempt_questions.first()
        original_prompt = row.question_snapshot["prompt_en"]
        original_correct = next(choice["text_en"] for choice in row.choices_snapshot if choice["is_correct"])
        row.question.prompt_en = "CHANGED BANK PROMPT"
        row.question.save(update_fields=["prompt_en"])
        current_correct = row.question.choices.get(is_correct=True)
        current_correct.text_en = "CHANGED BANK ANSWER"
        current_correct.save(update_fields=["text_en"])
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)
        self.client.force_login(self.user)

        response = self.client.get(reverse("assessments:result", args=[result.pk]) + "?lang=en")

        self.assertContains(response, original_prompt)
        self.assertContains(response, original_correct)
        self.assertNotContains(response, "CHANGED BANK PROMPT")
        self.assertNotContains(response, "CHANGED BANK ANSWER")

    def test_listening_transcript_is_revealed_only_on_result(self):
        Question.objects.filter(pk__in=[question.pk for question in self.questions]).update(
            question_type="listening", audio_path="assessments/audio/clip01.wav",
            transcript="Private transcript for post-assessment review.", max_plays=2,
        )
        attempt = self.start()
        self.client.force_login(self.user)
        attempt_page = self.client.get(attempt.get_absolute_url() + "?lang=en")
        self.assertNotContains(attempt_page, "Private transcript for post-assessment review.")
        attempt.status = "submitted"
        attempt.save(update_fields=["status"])
        result, _ = score_attempt(attempt.pk)

        result_page = self.client.get(reverse("assessments:result", args=[result.pk]) + "?lang=en")

        self.assertContains(result_page, "Show audio transcript")
        self.assertContains(result_page, "Private transcript for post-assessment review.")

    def test_complete_candidate_journey_from_start_to_report(self):
        self.client.force_login(self.user)
        start_response = self.client.post(reverse("assessments:start_attempt", args=[self.entitlement.pk]))
        attempt = Attempt.objects.get(entitlement=self.entitlement)
        self.assertRedirects(start_response, attempt.get_absolute_url() + "?lang=fa")
        self.assertContains(self.client.get(attempt.get_absolute_url()), "سؤال 1 / 2")
        self.assertContains(self.client.get(attempt.get_absolute_url()), "مرور پاسخ‌ها")
        for item in attempt.attempt_questions.select_related("question"):
            choice = item.question.choices.get(is_correct=True)
            answer_response = self.client.post(
                reverse("assessments:save_answer", args=[attempt.pk, item.pk]), {"choice": choice.pk}
            )
            self.assertEqual(answer_response.status_code, 200)
        finish_response = self.client.post(
            reverse("assessments:finish_attempt", args=[attempt.pk]),
            {"confirm_submission": "yes"},
        )
        result = AttemptResult.objects.get(attempt=attempt)
        self.assertRedirects(finish_response, reverse("assessments:result", args=[result.pk]) + "?lang=fa")
        report = self.client.get(reverse("assessments:result", args=[result.pk]))
        self.assertContains(report, "100")
        self.assertEqual(result.percentage, 100)
