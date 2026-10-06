from datetime import timedelta
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone, translation
from accounts.models import User
from assessments.models import Exam, ExamEntitlement, ManualPaymentSubmission, Order, PaymentTransaction, SupportTicket
from contracts.models import ContractProposal
from .models import CaseTask, Customer, CustomerCase, CustomerEvent


class TodayTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.root = User.objects.create_superuser(username="today-root", email="today-root@example.test", password="test-safe")
        self.client.force_login(self.root)
        self.url = reverse("management_portal:dashboard")
        self.exam = Exam.objects.create(slug="today-test", title_fa="آزمون نمونه", title_en="Sample assessment", language_mode="bilingual")

    def account(self, number):
        return User.objects.create_user(username=f"today-{number}", email=f"today-{number}@example.test", mobile=f"98912000{number:04d}")

    def order(self, number, **kwargs):
        return Order.objects.create(user=self.account(number), exam=self.exam, amount_irr=kwargs.pop("amount_irr", 2000000), **kwargs)

    def test_totals_are_not_preview_lengths_and_all_group_is_paginated(self):
        for n in range(9):
            self.account(n)
        response = self.client.get(self.url)
        group = response.context["today_groups"][0]
        self.assertEqual(group["count"], 9)
        self.assertEqual(len(group["items"]), 3)
        self.assertContains(response, "?group=registered")
        response = self.client.get(self.url, {"group": "registered"})
        self.assertEqual(len(response.context["today_groups"][0]["items"]), 9)

    def test_ready_excludes_missing_revoked_expired_and_consumed_grants(self):
        self.order(0, status="paid")
        for n in range(1, 6):
            order = self.order(n, status="paid", amount_irr=0 if n == 1 else 2000000)
            ExamEntitlement.objects.create(user=order.user, exam=self.exam, order=order,
                revoked_at=timezone.now() if n == 3 else None,
                expires_at=timezone.now() - timedelta(days=1) if n == 4 else None,
                attempts_remaining=0 if n == 5 else 1)
            if n == 2:
                ManualPaymentSubmission.objects.create(order=order, payer_name="Receipt", reference_number="TODAY-OK", paid_at=timezone.now(), status="approved")
        response = self.client.get(self.url)
        ready = next(g for g in response.context["today_groups"] if g["key"] == "ready")
        self.assertEqual(ready["count"], 2)
        self.assertContains(response, "رایگان / هدیه")
        self.assertContains(response, "رسید تأییدشده")
        self.assertNotContains(response, "پرداخت کرده، شروع نکرده")

    def test_payment_queue_total_order_priority_and_exact_destination(self):
        for n in range(10):
            order = self.order(n)
            payment = ManualPaymentSubmission.objects.create(order=order, payer_name=f"Payer {n}", reference_number=f"TODAY-{n}", paid_at=timezone.now())
            ManualPaymentSubmission.objects.filter(pk=payment.pk).update(updated_at=timezone.now() - timedelta(minutes=20-n))
        response = self.client.get(self.url)
        self.assertEqual(response.context["queue_total"], 10)
        self.assertEqual(len(response.context["queues"]), 8)
        first = response.context["queues"][0]
        self.assertEqual(first["title"], "Payer 0")
        self.assertEqual(first["rank"], 0)
        target = self.client.get(first["url"])
        self.assertContains(target, 'id="payment-')
        self.assertContains(target, "TODAY-0")
        self.assertNotContains(target, "TODAY-9")
        self.assertEqual(next(g for g in response.context["today_groups"] if g["key"] == "pending")["count"], 0)

    def test_payment_role_cannot_see_results_or_registered_group(self):
        staff = User.objects.create_user(username="today-pay", email="today-pay@example.test", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="assessments", codename="view_manualpaymentsubmission"))
        self.client.force_login(staff)
        response = self.client.get(self.url, {"group": "registered"})
        self.assertEqual({g["key"] for g in response.context["today_groups"]}, {"pending", "ready"})
        self.assertNotContains(response, "Registered, no order")

    def test_recent_activity_uses_event_time_not_customer_update(self):
        customer = Customer.objects.create(name="Recorded")
        Customer.objects.create(name="No activity")
        event = CustomerEvent.objects.create(customer=customer, category="identity", event_type="test", title_fa="رویداد", title_en="Event", occurred_at=timezone.now()-timedelta(days=7))
        response = self.client.get(self.url)
        self.assertEqual(list(response.context["recent_customers"].values_list("pk", flat=True)), [customer.pk])
        self.assertEqual(response.context["recent_customers"][0].last_event_at, event.occurred_at)

    def test_overdue_open_ticket_is_not_hidden_by_old_in_review_previews(self):
        account = self.account(1)
        for n in range(8):
            ticket = SupportTicket.objects.create(user=account, subject=f"Review {n}", message="test", category="technical", status="in_review")
            SupportTicket.objects.filter(pk=ticket.pk).update(created_at=timezone.now()-timedelta(days=5))
        urgent = SupportTicket.objects.create(user=account, subject="Waiting first response", message="test", category="technical")
        SupportTicket.objects.filter(pk=urgent.pk).update(created_at=timezone.now()-timedelta(days=1))
        response = self.client.get(self.url)
        first = response.context["queues"][0]
        self.assertEqual(first["title"], urgent.subject)
        self.assertEqual(first["rank"], 1)
        self.assertEqual(response.context["queue_total"], 9)
        target = self.client.get(first["url"])
        self.assertContains(target, urgent.subject)
        self.assertNotContains(target, "Review 0")

    def test_dashboard_get_does_not_approve_receipts(self):
        order = self.order(1)
        payment = ManualPaymentSubmission.objects.create(order=order, payer_name="Unverified", reference_number="TODAY-NO-WRITE", paid_at=timezone.now())
        ManualPaymentSubmission.objects.filter(pk=payment.pk).update(updated_at=timezone.now()-timedelta(hours=1))
        self.client.get(self.url)
        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(payment.status, "pending")
        self.assertEqual(order.status, "pending")

    def test_account_drilldown_and_malformed_ids_keep_existing_permissions(self):
        account = self.account(1)
        account.is_active = False
        account.save(update_fields=["is_active"])
        response = self.client.get(self.url)
        item = next(row for row in response.context["queues"] if row["kind"] == "حساب")
        target = self.client.get(item["url"])
        self.assertEqual(list(target.context["pending_users"]), [account])
        for value in ("²", "9"*30, "-1"):
            self.assertEqual(self.client.get(reverse("management_portal:approvals"), {"payment": value}).status_code, 200)
            self.assertEqual(self.client.get(reverse("management_portal:assessment_support"), {"ticket": value}).status_code, 200)
        staff = User.objects.create_user(username="today-no-access", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(item["url"]).status_code, 403)

    def test_ready_manual_access_is_not_presented_as_bank_payment(self):
        order = self.order(1, status="paid")
        ExamEntitlement.objects.create(user=order.user, exam=self.exam, order=order)
        response = self.client.get("/en/management/")
        self.assertContains(response, "Access granted; transfer not verified")
        self.assertNotContains(response, "Approved receipt")

    def test_ready_verified_gateway_source_is_identified(self):
        order = self.order(1, status="paid")
        ExamEntitlement.objects.create(user=order.user, exam=self.exam, order=order)
        PaymentTransaction.objects.create(order=order, gateway="test", external_id="TODAY-GATEWAY", amount_irr=order.amount_irr, status="verified")
        self.assertContains(self.client.get("/en/management/"), "Verified gateway payment")

    def test_overdue_tasks_and_contracts_have_actionable_destinations(self):
        case = CustomerCase.objects.create(kind="general", customer_name="Case")
        CaseTask.objects.create(case=case, title="Follow up", created_by=self.root, due_at=timezone.now()-timedelta(days=1))
        proposal = ContractProposal.objects.create(customer_name="Contract customer", customer_phone="09120000000", project_title="Project", project_scope="Scope", amount_irr=100000, delivery_terms="One week", status="sent", created_by=self.root)
        ContractProposal.objects.filter(pk=proposal.pk).update(created_at=timezone.now()-timedelta(days=2))
        response = self.client.get(self.url)
        self.assertEqual(response.context["queue_total"], 2)
        self.assertEqual(response.context["queues"][0]["kind"], "قرارداد")
        for row in response.context["queues"]:
            self.assertEqual(row["rank"], 1)
            self.assertEqual(self.client.get(row["url"]).status_code, 200)

    def test_queries_do_not_grow_with_more_group_rows(self):
        self.order(1, status="paid")
        self.client.get(self.url)  # Warm permission/content-type caches.
        with CaptureQueriesContext(connection) as before:
            self.client.get(self.url)
        for n in range(2, 12):
            self.order(n, status="paid")
        with CaptureQueriesContext(connection) as after:
            self.client.get(self.url)
        self.assertEqual(len(before), len(after))

    def test_empty_today_and_reports_are_separate_and_bilingual(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["queue_total"], 0)
        self.assertLessEqual(len(response.context["today_summaries"]), 4)
        self.assertNotContains(response, 'data-notification-panel')
        reports = self.client.get(self.url, {"view": "reports"})
        self.assertContains(reports, 'data-notification-panel')
        en = self.client.get("/en/management/")
        self.assertContains(en, "Customer follow-ups")
        self.assertNotContains(en, "تأیید خودکار معطل")
