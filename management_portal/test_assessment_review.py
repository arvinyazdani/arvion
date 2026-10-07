from unittest.mock import patch

from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import User
from assessments.models import (
    Attempt, AttemptQuestion, AttemptResult, Exam, ExamEntitlement, ExamSection,
    ExamVersion, IntegrityEvent, ManualPaymentSubmission, Order, PaymentTransaction,
    Question, Skill, WelcomeAssessmentCredit,
)
from .assessment_review import order_evidence
from .models import Customer, CustomerContact, OperationalAudit


class AssessmentReviewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(username="review-admin", email="review-admin@example.test", password="safe-test")
        cls.buyer = User.objects.create_user(username="review-buyer", email="review-buyer@example.test", first_name="Sample", mobile="09120004322")
        cls.customer = Customer.objects.create(name="Sample customer")
        CustomerContact.objects.create(customer=cls.customer, user=cls.buyer, name="Sample contact")
        cls.exam = Exam.objects.create(slug="review-test", title_fa="آزمون نمونه", title_en="Sample assessment", language_mode="en")
        cls.version = ExamVersion.objects.create(exam=cls.exam, version=1)
        cls.order = Order.objects.create(user=cls.buyer, customer=cls.customer, exam=cls.exam, amount_irr=900000, subtotal_irr=2000000, discount_irr=1100000, status="paid")
        cls.entitlement = ExamEntitlement.objects.create(user=cls.buyer, exam=cls.exam, order=cls.order)
        cls.attempt = Attempt.objects.create(user=cls.buyer, exam=cls.exam, version=cls.version, entitlement=cls.entitlement, status="completed")
        AttemptResult.objects.create(attempt=cls.attempt, percentage=85, level_code="B2", level_title_fa="متوسط", level_title_en="Intermediate")
        cls.payment = ManualPaymentSubmission.objects.create(order=cls.order, payer_name="QA Payer", reference_number="REVIEW-TEST", paid_at=timezone.now(), note="Declared transfer")

    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.client.force_login(self.admin)
        self.list_url = reverse("management_portal:assessment_support")
        self.report_url = reverse("management_portal:assessment_attempt_detail", args=[self.attempt.pk])
        self.payments_url = reverse("management_portal:approvals")

    def attempt_row(self, index, status="ready"):
        order = Order.objects.create(user=self.buyer, customer=self.customer, exam=self.exam, amount_irr=900000, status="paid")
        entitlement = ExamEntitlement.objects.create(user=self.buyer, exam=self.exam, order=order)
        return Attempt.objects.create(user=self.buyer, exam=self.exam, version=self.version, entitlement=entitlement, status=status)

    def question(self, *, timed=True, correct=True):
        skill = Skill.objects.create(exam=self.exam, code="qa", title_fa="مهارت", title_en="Skill")
        section = ExamSection.objects.create(version=self.version, code="qa", title_fa="بخش", title_en="Section", question_count=1)
        question = Question.objects.create(version=self.version, section=section, skill=skill, prompt_fa="پرسش", prompt_en="Question")
        return AttemptQuestion.objects.create(
            attempt=self.attempt, question=question, position=1,
            question_snapshot={"difficulty": 5, "suggested_seconds": 60, "prompt_en": "Exact QA prompt", "explanation_en": "PRIVATE-EXPLANATION"},
            choices_snapshot=[{"id": 101, "is_correct": correct, "text_en": "PRIVATE-ANSWER-KEY"}], selected_choice_snapshot_id=101,
            answered_at=timezone.now(), active_seconds=12 if timed else 0,
            first_seen_at=timezone.now() if timed else None, visit_count=2, answer_change_count=1,
        )

    def test_filters_counts_and_direct_report(self):
        self.attempt_row(1)
        response = self.client.get(self.list_url, {"status": "completed", "q": "Sample", "exam": self.exam.pk})
        self.assertEqual(response.context["attempt_page"].paginator.count, 1)
        self.assertContains(response, self.report_url)
        self.assertContains(response, "85.00%")
        empty = self.client.get(self.list_url, {"q": "missing"})
        self.assertContains(empty, "تلاشی با این فیلتر پیدا نشد")
        self.assertEqual(self.client.get(self.list_url, {"exam": "²", "status": "bad", "attempts_page": "bad"}).status_code, 200)

    def test_pagination_preserves_filter_and_reaches_older_attempt(self):
        for n in range(21):
            self.attempt_row(n, "completed")
        response = self.client.get(self.list_url, {"status": "completed", "q": "Sample", "attempts_page": 2})
        self.assertEqual(response.context["attempt_page"].paginator.count, 22)
        self.assertEqual(len(response.context["attempts"]), 2)
        self.assertContains(response, self.report_url)
        self.assertContains(response, "status=completed")
        self.assertContains(response, "q=Sample")

    def test_report_has_explained_evidence_and_no_answer_key(self):
        question = self.question()
        IntegrityEvent.objects.create(attempt=self.attempt, attempt_question=question, event_type="copy", metadata={"reason_fa": "دلیل تاریخی", "reason_en": "Historical reason", "pairing_status": "not_applicable"})
        response = self.client.get(self.report_url)
        self.assertContains(response, "Exact QA prompt")
        self.assertContains(response, "بسیار دشوار")
        self.assertContains(response, "دلیل تاریخی")
        self.assertContains(response, "نه اثبات تقلب")
        self.assertContains(response, 'data-label="فعال / انتظار"')
        self.assertContains(response, 'data-confirm=')
        for value in ("PRIVATE-ANSWER-KEY", "PRIVATE-EXPLANATION", '"is_correct"'):
            self.assertNotContains(response, value)
        self.assertEqual(len(response.context["attempts"]), 1)

    def test_legacy_missing_timing_is_not_invented(self):
        self.question(timed=False)
        response = self.client.get(self.report_url)
        self.assertContains(response, "برای تلاش‌های قدیمی ثبت نشده")
        self.assertContains(response, "بدون داده زمان")
        self.assertContains(response, "داده‌های پایش ناقص یا قدیمی")

    def test_copy_report_separates_legacy_count_and_explains_stop_in_both_languages(self):
        item = self.question()
        self.order.gateway = "welcome_trial"
        self.order.save(update_fields=["gateway"])
        WelcomeAssessmentCredit.objects.create(user=self.buyer, order=self.order)
        self.attempt.status = "invalidated"
        self.attempt.completion_reason = "copy_limit"
        self.attempt.submitted_at = timezone.now()
        self.attempt.save()
        AttemptResult.objects.filter(attempt=self.attempt).delete()
        IntegrityEvent.objects.create(attempt=self.attempt, event_type="other", metadata={
            "kind": "copy_policy_acceptance", "copy_policy_version": 2})
        IntegrityEvent.objects.create(attempt=self.attempt, attempt_question=item, event_type="copy")
        for n in range(5):
            IntegrityEvent.objects.create(attempt=self.attempt, attempt_question=item, event_type="copy",
                metadata={"copy_policy_version": 1, "copy_event_id": f"qa-copy-{n}"})
        IntegrityEvent.objects.create(attempt=self.attempt, event_type="other", metadata={
            "kind": "welcome_copy_stop", "reason_fa": "پاسخ‌ها محفوظ‌اند", "reason_en": "Answers retained"})
        for lang in ("fa", "en"):
            response = self.client.get(self.report_url.replace("/fa/", f"/{lang}/"))
            policy = response.context["attempts"][0].management_copy
            self.assertEqual((policy["count"], policy["legacy_count"], policy["last_question"]), (5, 1, 1))
            self.assertTrue(policy["enabled"])
            self.assertTrue(policy["stopped"])
            self.assertIsNotNone(policy["acknowledged_at"])
            self.assertContains(response, "تلاش کپی شماره 5" if lang == "fa" else "Copy attempt 5")
            self.assertContains(response, "توقف خودکار آزمون هدیه" if lang == "fa" else "Automatic welcome assessment stop")
            self.assertContains(response, "حساب مسدود نشده" if lang == "fa" else "account is not blocked")
            self.assertContains(response, "سابقه قطعی عملیات سرور" if lang == "fa" else "Server operation audit")
            self.assertNotContains(response, "نتیجه نهایی هنوز تولید نشده" if lang == "fa" else "The final result is not ready")
            self.assertNotContains(response, "qa-copy-")

    def test_paid_and_old_gifts_report_no_five_copy_stop(self):
        item = self.question()
        IntegrityEvent.objects.create(attempt=self.attempt, attempt_question=item, event_type="copy",
            metadata={"copy_policy_version": 1})
        for gateway in ("card_transfer", "welcome_trial"):
            self.order.gateway = gateway
            self.order.save(update_fields=["gateway"])
            response = self.client.get(self.report_url)
            self.assertFalse(response.context["attempts"][0].management_copy["enabled"])
            self.assertContains(response, "بدون توقف پنج‌تلاشی")

    def test_prefetched_legacy_copy_report_performs_no_policy_lookup(self):
        from assessments.integrity import copy_policy_report
        attempt = Attempt.objects.prefetch_related('integrity_events__attempt_question').get(pk=self.attempt.pk)
        with self.assertNumQueries(0):
            report = copy_policy_report(attempt)
        self.assertFalse(report['enabled'])
        self.assertEqual(report['count'], 0)

    def test_report_without_customer_is_read_only_and_available(self):
        CustomerContact.objects.filter(user=self.buyer).update(user=None)
        Order.objects.filter(pk=self.order.pk).update(customer=None)
        counts = [m.objects.count() for m in (Customer, CustomerContact, OperationalAudit)]
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.list_url)
        self.assertNotContains(response, "revoke-access/")
        self.assertEqual(counts, [m.objects.count() for m in (Customer, CustomerContact, OperationalAudit)])

    def test_report_cannot_mix_foreign_attempt_or_expose_to_nonstaff(self):
        other = self.attempt_row(2)
        response = self.client.get(self.report_url)
        self.assertNotContains(response, f'id="attempt-{other.pk}"')
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(self.report_url).status_code, 302)

    def test_specific_account_drilldown_bypasses_page_and_rejects_foreign_ids(self):
        for n in range(21):
            self.attempt_row(n)
        url = reverse("management_portal:customer_assessment_detail", args=[self.customer.pk, self.buyer.pk])
        response = self.client.get(url, {"attempt": self.attempt.pk})
        self.assertContains(response, f'id="attempt-{self.attempt.pk}"')
        self.assertEqual(len(response.context["attempts"]), 1)
        self.assertContains(self.client.get(url, {"order": self.order.pk}), f'id="order-{self.order.pk}"')
        foreign = User.objects.create_user(username="review-other")
        order = Order.objects.create(user=foreign, exam=self.exam, amount_irr=1)
        self.assertEqual(self.client.get(url, {"order": order.pk}).status_code, 404)
        self.assertEqual(self.client.get(url, {"attempt": "bad-uuid"}).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.report_url).status_code, 302)

    def test_support_only_role_cannot_read_new_report(self):
        staff = User.objects.create_user(username="review-support", email="support@example.test", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="assessments", codename="view_supportticket"))
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertEqual(self.client.get(self.report_url).status_code, 403)
        self.assertNotContains(self.client.get(self.list_url), "review-test")

    def test_payment_detail_identity_decision_history_and_scoped_audit(self):
        OperationalAudit.objects.create(actor=self.admin, action="payment_reject", target_type="manual_payment", target_id=str(self.payment.pk), summary="QA rejection")
        OperationalAudit.objects.create(actor=self.admin, action="payment_approve", target_type="manual_payment", target_id="99999", summary="PRIVATE-FOREIGN-AUDIT")
        response = self.client.get(self.payments_url, {"payment": self.payment.pk})
        for value in (self.buyer.email, self.buyer.mobile, "QA Payer", "REVIEW-TEST", "Declared transfer", "900,000", "رد رسید", self.admin.email, "سابقه عملیات مدیران"):
            self.assertContains(response, value)
        self.assertEqual(response.context["payments"][0].history_count, 1)
        self.assertNotContains(response, "PRIVATE-FOREIGN-AUDIT")
        self.assertContains(response, reverse("management_portal:customer_detail", args=[self.customer.pk]))

    def test_gift_automatic_manual_and_unknown_sources_are_distinct(self):
        def evidence():
            order = Order.objects.select_related("manual_payment", "entitlement").prefetch_related("transactions").get(pk=self.order.pk)
            return order_evidence(order, "fa")["source"]
        Order.objects.filter(pk=self.order.pk).update(gateway="welcome_trial", amount_irr=0)
        self.assertIn("هدیه ثبت‌نام", evidence())
        Order.objects.filter(pk=self.order.pk).update(gateway="card_transfer", amount_irr=900000)
        ManualPaymentSubmission.objects.filter(pk=self.payment.pk).update(status="approved")
        self.assertIn("روش بررسی ثبت نشده", evidence())
        transaction = PaymentTransaction.objects.create(order=self.order, gateway="card_transfer", external_id="QA-CARD", amount_irr=900000, status="verified", raw_response={"automatic_review": True, "token": "PRIVATE-PROVIDER-TOKEN"})
        self.assertIn("تأیید خودکار", evidence())
        response = self.client.get(self.payments_url, {"payment": self.payment.pk})
        self.assertNotContains(response, "PRIVATE-PROVIDER-TOKEN")
        transaction.raw_response = {"manual_review": True}
        transaction.save()
        ManualPaymentSubmission.objects.filter(pk=self.payment.pk).update(reviewed_by=self.admin)
        self.assertIn("توسط مدیر", evidence())

    def test_manual_legacy_grant_does_not_claim_bank_payment(self):
        ManualPaymentSubmission.objects.filter(pk=self.payment.pk).update(status="rejected")
        response = self.client.get(self.report_url)
        self.assertContains(response, "رسید ردشده")
        self.assertContains(response, "دسترسی صادر شده")
        self.assertNotContains(response, "تراکنش تأییدشده درگاه")

    def test_payment_filters_pagination_and_missing_exact_receipt(self):
        for n in range(21):
            attempt = self.attempt_row(n)
            ManualPaymentSubmission.objects.create(order=attempt.entitlement.order, payer_name="QA", reference_number=f"BATCH-{n}", paid_at=timezone.now(), status="rejected")
        response = self.client.get(self.payments_url, {"payment_status": "rejected", "q": "BATCH", "payments_page": 2})
        self.assertEqual(response.context["payment_page"].paginator.count, 21)
        self.assertEqual(len(response.context["payments"]), 1)
        self.assertContains(response, "payment_status=rejected")
        self.assertNotContains(response, "REVIEW-TEST")
        self.assertContains(self.client.get(self.payments_url, {"payment": 99999}), "رسیدی مطابق این انتخاب پیدا نشد")

    @patch("management_portal.views.send_mail")
    def test_payment_decision_returns_exact_receipt_is_audited_and_replay_safe(self, _mail):
        Order.objects.filter(pk=self.order.pk).update(status="pending", gateway="card_transfer", terms_version="qa", terms_accepted_at=timezone.now())
        path = reverse("management_portal:payment_review", args=[self.payment.pk, "approve"])
        data = {"review_note": "QA confirmed", "return_payment": "1", "inbox_return": "https://evil.invalid"}
        response = self.client.post(path, data)
        self.assertEqual(response.url, self.payments_url + f"?payment={self.payment.pk}#payment-{self.payment.pk}")
        self.client.post(path, data)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "approved")
        self.assertEqual(self.payment.review_note, "QA confirmed")
        self.assertEqual(PaymentTransaction.objects.filter(order=self.order, status="verified").count(), 1)
        self.assertEqual(OperationalAudit.objects.filter(action="payment_approve", target_id=str(self.payment.pk)).count(), 1)

    def test_read_only_payment_role_and_csrf_cannot_decide(self):
        staff = User.objects.create_user(username="review-viewer", email="review-viewer@example.test", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="assessments", codename="view_manualpaymentsubmission"))
        self.client.force_login(staff)
        response = self.client.get(self.payments_url, {"payment": self.payment.pk})
        self.assertEqual(response.status_code, 200)
        path = reverse("management_portal:payment_review", args=[self.payment.pk, "reject"])
        self.assertNotContains(response, path)
        self.assertEqual(self.client.post(path).status_code, 403)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(path).status_code, 403)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    def test_english_report_uses_english_labels_and_ltr_prompt(self):
        self.question(correct=False)
        response = self.client.get(f"/en/management/assessment-support/attempts/{self.attempt.pk}/")
        for value in ("Incorrect answer", "Expert", "Sample assessment", 'dir="ltr"', "not proof of cheating"):
            self.assertContains(response, value)
        self.assertNotContains(response, "آزمون نمونه")
        self.assertNotContains(response, "PRIVATE-ANSWER-KEY")

    def test_list_and_payment_queries_do_not_grow_per_row(self):
        for url in (self.list_url, self.payments_url):
            self.client.get(url)
        with CaptureQueriesContext(connection) as before:
            self.client.get(self.list_url)
            self.client.get(self.payments_url)
        for n in range(7):
            attempt = self.attempt_row(n)
            ManualPaymentSubmission.objects.create(order=attempt.entitlement.order, payer_name="Batch", reference_number=f"NPLUS-{n}", paid_at=timezone.now())
        with CaptureQueriesContext(connection) as after:
            self.client.get(self.list_url)
            self.client.get(self.payments_url)
        self.assertLessEqual(len(after), len(before) + 1)
