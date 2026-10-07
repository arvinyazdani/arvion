from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth.models import Permission
from django.core import signing
from django.db import close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import User
from assessments.models import Attempt, Exam, ExamEntitlement, ExamVersion, Order
from core.sms.backends import SMSDeliveryError, SMSResult
from traffic.models import TrafficDay
from .customer_analytics import build_customer_funnel
from .customer_segments import apply_customer_filters, normalize_segment_filters
from .models import CaseActivity, CaseTask, Customer, CustomerCase, OperationalAudit, SMSCampaign, SMSDispatch
from .sms_audiences import resolve_sms_audience
from .sms_preview import claim_campaign, SALT


class FollowupTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.root = User.objects.create_superuser(username="followup-qa", email="followup-qa@example.test", password="test-only")
        self.client.force_login(self.root)
        self.sms_url = reverse("management_portal:sms_send")
        self.task_url = reverse("management_portal:followup_list")
        self.case = CustomerCase.objects.create(kind="general", customer_name="QA case")

    def preview(self, **kwargs):
        data = {"audience": "manual", "recipients": "09120001122", "message": "QA message", "action": "preview"}
        data.update(kwargs)
        response = self.client.post(self.sms_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["preview"], response.context["form"].errors)
        return dict(data, action="send", confirm="on", preview_token=response.context["preview"]["token"])

    @patch("management_portal.views.send_sms")
    def test_preview_has_no_external_or_campaign_side_effect(self, send):
        self.preview()
        send.assert_not_called()
        self.assertFalse(SMSCampaign.objects.exists())
        self.assertFalse(OperationalAudit.objects.filter(action__startswith="sms_campaign").exists())
        response = self.client.post(self.sms_url, {"audience": "manual", "recipients": "09120001122", "message": "QA", "action": "preview", "confirm": "on"})
        self.assertNotIn('checked', str(response.context["form"]["confirm"]))

    @patch("management_portal.views.send_sms", return_value=SMSResult(provider="mock", reference="mock"))
    def test_repeat_confirm_is_at_most_once(self, send):
        data = self.preview()
        self.assertEqual(self.client.post(self.sms_url, data).status_code, 302)
        self.assertEqual(self.client.post(self.sms_url, data).status_code, 302)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(SMSCampaign.objects.count(), 1)
        self.assertEqual(SMSDispatch.objects.count(), 1)
        self.assertEqual(OperationalAudit.objects.filter(action="sms_campaign_sent").count(), 1)

    @patch("management_portal.views.send_sms")
    def test_changed_membership_same_count_is_rejected(self, send):
        member = User.objects.create_user(username="qa-recipient", email="qa-recipient@example.test", mobile="09120001122")
        data = self.preview(audience="registered", recipients="", expected_count="1")
        member.mobile = "09120001123"
        member.save(update_fields=["mobile"])
        response = self.client.post(self.sms_url, data)
        self.assertContains(response, "متن یا اعضای گروه تغییر کرده‌اند")
        send.assert_not_called()
        self.assertFalse(SMSCampaign.objects.exists())

    @patch("management_portal.views.send_sms")
    def test_changed_message_and_missing_confirmation_are_rejected(self, send):
        data = self.preview()
        response = self.client.post(self.sms_url, dict(data, message="changed"))
        self.assertContains(response, "متن یا اعضای گروه تغییر کرده‌اند")
        self.client.post(self.sms_url, dict(data, confirm=""))
        send.assert_not_called()
        self.assertFalse(SMSCampaign.objects.exists())

    @patch("management_portal.views.send_sms")
    def test_expired_and_other_actor_preview_rejected(self, send):
        data = self.preview()
        with patch("django.core.signing.time.time", return_value=timezone.now().timestamp()+901):
            self.assertEqual(self.client.post(self.sms_url, data).status_code, 200)
        other = User.objects.create_superuser(username="qa-other", email="qa-other@example.test", password="test-only")
        self.client.force_login(other)
        self.assertEqual(self.client.post(self.sms_url, data).status_code, 200)
        send.assert_not_called()
        self.assertFalse(SMSCampaign.objects.exists())
        decoded = signing.loads(data["preview_token"], salt=SALT)
        self.assertEqual(set(decoded), {"actor", "nonce", "digest"})
        self.assertNotIn("QA message", str(decoded))
        self.assertNotIn("09120001122", str(decoded))

    @patch("management_portal.views.send_sms", side_effect=SMSDeliveryError("SECRET_SHOULD_NOT_BE_STORED"))
    def test_provider_failure_is_audited_without_raw_secrets_and_not_retried(self, send):
        data = self.preview()
        self.client.post(self.sms_url, data)
        self.client.post(self.sms_url, data)
        self.assertEqual(send.call_count, 1)
        campaign = SMSCampaign.objects.get()
        self.assertEqual((campaign.sent_count, campaign.failed_count), (0, 1))
        self.assertEqual(SMSDispatch.objects.get().error_message, "SMSDeliveryError")
        self.assertNotContains(self.client.get(self.sms_url), "SECRET_SHOULD_NOT_BE_STORED")

    @patch("management_portal.views.send_sms")
    def test_unknown_outcome_retains_claim_without_retry(self, send):
        data = self.preview()
        send.side_effect = RuntimeError("unexpected")
        with self.assertRaises(RuntimeError):
            self.client.post(self.sms_url, data)
        send.reset_mock()
        self.client.post(self.sms_url, data)
        send.assert_not_called()
        self.assertEqual(SMSCampaign.objects.count(), 1)
        self.assertContains(self.client.get(self.sms_url), "نتیجه 1 ارسال هنوز ثبت نشده")

    @patch("management_portal.views.send_sms", return_value=SMSResult(provider="mock", reference="mock"))
    def test_live_audience_allows_50_while_manual_limit_stays_20(self, send):
        for i in range(50):
            User.objects.create_user(username=f"qa50-{i}", email=f"qa50-{i}@example.test", mobile=f"0912000{i:04d}")
        data = self.preview(audience="registered", recipients="", expected_count="50")
        self.client.post(self.sms_url, data)
        self.assertEqual(send.call_count, 50)
        send.reset_mock()
        response = self.client.post(self.sms_url, {"recipients": "\n".join(f"0912001{i:04d}" for i in range(21)), "message": "QA", "action": "preview"})
        self.assertTrue(response.context["form"].errors)
        send.assert_not_called()

    def test_sms_permissions_and_csrf(self):
        ordinary = User.objects.create_user(username="qa-staff", email="qa-staff@example.test", is_staff=True)
        self.client.force_login(ordinary)
        self.assertEqual(self.client.post(self.sms_url, {"action": "preview"}).status_code, 403)
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.root)
        self.assertEqual(csrf_client.post(self.sms_url, {"action": "preview"}).status_code, 403)

    def test_history_is_paginated_with_totals(self):
        SMSCampaign.objects.bulk_create([SMSCampaign(created_by=self.root, message="QA", audience="manual", recipient_count=1) for _ in range(21)])
        response = self.client.get(self.sms_url+"?campaign_page=2")
        self.assertEqual(response.context["campaigns"].paginator.count, 21)
        self.assertEqual(len(response.context["campaigns"]), 1)
        self.assertContains(response, "campaign_page=1")

    def test_task_invalid_retains_values_and_success_is_audited(self):
        response = self.client.post(self.task_url, {"case": "no", "title": "Typed title", "priority": "urgent"})
        self.assertContains(response, "Typed title")
        self.assertFalse(CaseTask.objects.exists())
        response = self.client.post(self.task_url, {"case": self.case.pk, "title": "QA follow-up", "priority": "urgent", "assigned_to": self.root.pk})
        self.assertEqual(response.status_code, 302)
        task = CaseTask.objects.get()
        self.assertEqual(task.assigned_to, self.root)
        self.assertTrue(OperationalAudit.objects.filter(action="followup_task_created", target_id=str(task.pk)).exists())

    def test_task_explicit_status_is_idempotent_and_cancelled_is_protected(self):
        task = CaseTask.objects.create(case=self.case, created_by=self.root, title="QA")
        url = reverse("management_portal:followup_task_status", args=[task.pk])
        self.client.post(url, {"status": "done"})
        self.client.post(url, {"status": "done"})
        task.refresh_from_db()
        self.assertEqual(task.status, "done")
        self.assertEqual(OperationalAudit.objects.filter(action="followup_task_status").count(), 1)
        self.assertEqual(CaseActivity.objects.filter(case=self.case, title="وضعیت وظیفه تغییر کرد").count(), 1)
        task.status = "cancelled"
        task.save(update_fields=["status"])
        self.assertEqual(self.client.post(url, {"status": "done"}).status_code, 302)
        task.refresh_from_db()
        self.assertEqual(task.status, "cancelled")
        self.assertEqual(self.client.get(url).status_code, 405)

    def test_task_permissions_filters_and_ordering(self):
        early = CaseTask.objects.create(case=self.case, created_by=self.root, assigned_to=self.root, title="QA early", due_at=timezone.now()-timedelta(days=1))
        CaseTask.objects.create(case=self.case, created_by=self.root, title="QA undated", priority="urgent")
        self.assertEqual(self.client.get(self.task_url).context["tasks"][0], early)
        self.assertEqual(self.client.get(self.task_url+"?state=overdue").context["tasks"].paginator.count, 1)
        self.assertEqual(self.client.get(self.task_url+"?state=mine").context["tasks"].paginator.count, 1)
        staff = User.objects.create_user(username="qa-readonly", email="qa-readonly@example.test", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.task_url).status_code, 200)
        self.assertNotContains(self.client.get(self.task_url), 'name="status"')
        self.assertEqual(self.client.post(self.task_url, {"case": self.case.pk, "title": "QA", "priority": "normal"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("management_portal:followup_task_status", args=[early.pk]), {"status": "done"}).status_code, 403)
        staff.user_permissions.add(Permission.objects.get(codename="change_customercase"))
        self.assertEqual(self.client.post(reverse("management_portal:followup_task_status", args=[early.pk]), {"status": "done"}).status_code, 302)

    def test_ready_audience_requires_valid_unstarted_entitlement(self):
        exam = Exam.objects.create(slug="qa-ready", title_fa="QA", title_en="QA")
        users = []
        for i in range(5):
            user = User.objects.create_user(username=f"qa-ready-{i}", email=f"qa-ready-{i}@example.test", mobile=f"0912000200{i}")
            users.append(user)
            customer = Customer.objects.create(name=f"QA {i}", phone=user.mobile)
            order = Order.objects.create(customer=customer, user=user, exam=exam, amount_irr=1, status="paid")
            if i:
                ExamEntitlement.objects.create(user=user, exam=exam, order=order,
                    revoked_at=timezone.now() if i == 1 else None,
                    expires_at=timezone.now()-timedelta(days=1) if i == 2 else None,
                    attempts_remaining=0 if i == 3 else 1)
        self.assertEqual(resolve_sms_audience("ready").recipients, ("989120002004",))
        self.assertEqual(list(apply_customer_filters(Customer.objects.all(), {"journey": "ready"}).values_list("phone", flat=True)), [users[4].mobile])
        report = build_customer_funnel()
        self.assertEqual(next(row for row in report["bottlenecks"] if row["key"] == "ready")["count"], 1)
        self.assertEqual(normalize_segment_filters({"journey": "in_progress"})["journey"], "in_progress")

    def test_reports_traffic_terms_and_decimal_style_are_localized(self):
        TrafficDay.objects.create(date=timezone.localdate(), page_views=7, unique_visitors=3)
        response = self.client.get(reverse("management_portal:customer_reports"))
        self.assertContains(response, "بازدید صفحه: 7")
        self.assertContains(response, "مدرک واریز نیست")
        response = self.client.get("/en/management/customers/reports/")
        self.assertContains(response, "Sum of daily visitors: 3")
        self.assertContains(response, "not proof of bank payment")

    def test_case_picker_is_bounded_searchable_and_preserves_older_selection(self):
        CustomerCase.objects.bulk_create([CustomerCase(kind="general", customer_name=f"QA case {i}") for i in range(120)])
        self.assertEqual(len(self.client.get(self.task_url).context["cases"]), 100)
        found = self.client.get(self.task_url+"?case_q="+self.case.code)
        self.assertEqual(list(found.context["cases"]), [self.case])
        invalid = self.client.post(self.task_url, {"case": self.case.pk, "title": "", "priority": "normal"})
        self.assertIn(self.case, list(invalid.context["cases"]))
        self.assertContains(invalid, 'id="id_title-errors"')
        huge = self.client.post(self.task_url, {"case": "9"*100, "title": "QA", "priority": "normal"})
        self.assertEqual(huge.status_code, 200)
        self.assertEqual(self.client.post(self.task_url, {"case": "²", "title": "QA", "priority": "normal"}).status_code, 200)
        self.assertFalse(CaseTask.objects.exists())

    def test_in_progress_link_matches_report_and_another_exam_does_not_hide_ready(self):
        user = User.objects.create_user(username="qa-two-exams", email="qa-two-exams@example.test", mobile="09120001122")
        customer = Customer.objects.create(name="QA two exams")
        exams = [Exam.objects.create(slug=f"qa-exam-{i}", title_fa="QA", title_en="QA") for i in range(2)]
        for i, exam in enumerate(exams):
            order = Order.objects.create(user=user, customer=customer, exam=exam, status="paid", amount_irr=1)
            entitlement = ExamEntitlement.objects.create(user=user, exam=exam, order=order)
            if i == 0:
                version = ExamVersion.objects.create(exam=exam, version=1)
                Attempt.objects.create(user=user, exam=exam, version=version, entitlement=entitlement, status="in_progress", started_at=timezone.now())
        self.assertEqual(resolve_sms_audience("ready").count, 1)
        members = apply_customer_filters(Customer.objects.all(), {"journey": "in_progress"})
        self.assertEqual(list(members), [customer])
        report = build_customer_funnel()
        self.assertEqual(next(row for row in report["bottlenecks"] if row["key"] == "in_progress")["count"], members.count())


class CampaignClaimConcurrencyTests(TransactionTestCase):
    def test_sms_view_is_non_atomic_and_claim_survives_provider_exception(self):
        from django.urls import resolve
        self.assertIn("default", resolve(reverse("management_portal:sms_send")).func._non_atomic_requests)
        user = User.objects.create_superuser(username="qa-transaction", email="qa-transaction@example.test", password="test-only")
        self.client.force_login(user)
        url = reverse("management_portal:sms_send")
        data = {"audience": "manual", "recipients": "09120001122", "message": "QA", "action": "preview"}
        preview = self.client.post(url, data)
        data.update(action="send", confirm="on", preview_token=preview.context["preview"]["token"])
        def fail(recipient, message):
            self.assertFalse(connection.in_atomic_block)
            self.assertTrue(SMSCampaign.objects.filter(created_by=user).exists())
            raise RuntimeError("injected provider interruption")
        with patch("management_portal.views.send_sms", side_effect=fail):
            with self.assertRaises(RuntimeError):
                self.client.post(url, data)
        self.assertEqual(SMSCampaign.objects.filter(created_by=user).count(), 1)

    def test_postgresql_only_one_concurrent_claim_wins(self):
        if connection.vendor != "postgresql":
            self.skipTest("Requires real PostgreSQL concurrency.")
        user = User.objects.create_superuser(username="qa-race", email="qa-race@example.test", password="test-only")
        token, barrier = uuid4(), Barrier(2)
        def worker():
            close_old_connections()
            try:
                actor = User.objects.get(pk=user.pk)
                barrier.wait(timeout=10)
                campaign, claimed = claim_campaign(token, actor, "manual", ["989120001122"], "QA")
                return campaign.pk, claimed
            finally:
                close_old_connections()
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: worker(), range(2)))
        self.assertEqual(len({pk for pk, claimed in results}), 1)
        self.assertEqual(sum(claimed for pk, claimed in results), 1)
        self.assertEqual(SMSCampaign.objects.count(), 1)


class CampaignMigrationTests(TransactionTestCase):
    def test_nullable_token_forward_and_rollback_preserve_legacy_campaign(self):
        user = User.objects.create_superuser(username="qa-migration", email="qa-migration@example.test", password="test-only")
        before = [("management_portal", "0019_notification_lifecycle")]
        after = [("management_portal", "0020_sms_campaign_submission_token")]
        executor = MigrationExecutor(connection)
        try:
            executor.migrate(before)
            legacy_model = executor.loader.project_state(before).apps.get_model("management_portal", "SMSCampaign")
            campaign = legacy_model.objects.create(created_by_id=user.pk, audience="manual", message="QA legacy", recipient_count=2, sent_count=1, failed_count=1)
            pk = campaign.pk
            executor = MigrationExecutor(connection)
            executor.migrate(after)
            current = executor.loader.project_state(after).apps.get_model("management_portal", "SMSCampaign")
            row = current.objects.get(pk=pk)
            self.assertIsNone(row.submission_token)
            self.assertEqual((row.sent_count, row.failed_count, row.message), (1, 1, "QA legacy"))
            executor = MigrationExecutor(connection)
            executor.migrate(before)
            restored = executor.loader.project_state(before).apps.get_model("management_portal", "SMSCampaign").objects.get(pk=pk)
            self.assertEqual((restored.sent_count, restored.failed_count, restored.message), (1, 1, "QA legacy"))
        finally:
            MigrationExecutor(connection).migrate(after)
