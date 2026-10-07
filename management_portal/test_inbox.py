from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth.models import Permission
from django.test import Client, TestCase, TransactionTestCase
from django.db import connection, connections, close_old_connections
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import User
from assessments.models import Exam, ExamEntitlement, ManualPaymentSubmission, Order, PaymentTransaction, SupportTicket
from contracts.models import ContractProposal, ContractReview, ContractVersion
from .inbox import present_sources, safe_inbox_return
from .models import Customer, CustomerContact, ManagementNotification, NotificationReceipt, OperationalAudit


class WorkInboxTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.admin = User.objects.create_superuser(username="inbox-qa", email="inbox-qa@example.test", password="safe-test")
        self.client.force_login(self.admin)
        self.buyer = User.objects.create_user(username="inbox-buyer", email="inbox-buyer@example.test", first_name="خریدار")
        self.exam = Exam.objects.create(slug="inbox-test", title_fa="آزمون", title_en="Test", language_mode="bilingual")
        self.order = Order.objects.create(user=self.buyer, exam=self.exam, amount_irr=2000000, gateway="card_transfer", terms_version="v1", terms_accepted_at=timezone.now())
        self.payment = ManualPaymentSubmission.objects.create(order=self.order, payer_name="واریزکننده", reference_number="INBOX-REF-1", paid_at=timezone.now())
        self.alert = ManagementNotification.objects.get(source_key=f"payment:{self.payment.pk}")
        self.url = reverse("management_portal:notification_list")

    def open(self, item, **params):
        return self.client.get(reverse("management_portal:notification_open", args=[item.pk]), params)

    def test_payment_opens_exact_receipt_seen_is_not_resolved(self):
        response = self.open(self.alert)
        self.assertEqual(response.url, reverse("management_portal:approvals") + f"?payment={self.payment.pk}#payment-{self.payment.pk}")
        self.alert.refresh_from_db()
        self.payment.refresh_from_db()
        self.assertEqual(self.alert.status, "unread")
        self.assertEqual(self.payment.status, "pending")
        self.assertIsNotNone(NotificationReceipt.objects.get(user=self.admin, notification=self.alert).seen_at)

    def test_payment_card_has_evidence_and_only_pending_receipt_has_decisions(self):
        response = self.client.get(self.url, {"category": "payments"})
        for value in ("واریزکننده", "INBOX-REF-1", "2,000,000", "خریدار"):
            self.assertContains(response, value)
        self.assertContains(response, f"/notifications/{self.alert.pk}/payment/approve/")
        self.assertNotContains(response, f"/notifications/{self.alert.pk}/resolved/")
        ManualPaymentSubmission.objects.filter(pk=self.payment.pk).update(status="approved")
        self.assertNotContains(self.client.get(self.url), f"/notifications/{self.alert.pk}/payment/approve/")

    def test_missing_receipt_disables_decision_and_has_recovery(self):
        missing = ManagementNotification.objects.create(category="payments", source_key="payment:999999", title="Missing")
        response = self.client.get(self.url)
        self.assertContains(response, "منبع در دسترس نیست")
        self.assertNotContains(response, f"/notifications/{missing.pk}/payment/approve/")
        self.assertRedirects(self.open(missing), self.url)

    def test_parser_cannot_target_a_receipt_from_an_unrelated_key(self):
        forged = ManagementNotification.objects.create(category="payments", source_key=f"other:{self.payment.pk}", title="Unrelated")
        response = self.client.post(reverse("management_portal:notification_payment_action", args=[forged.pk, "approve"]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 400)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    def test_resubmission_and_sla_are_one_work_item_without_deleting_history(self):
        ManagementNotification.objects.create(category="payments", source_key=f"payment:{self.payment.pk}:resubmitted:123", title="Resubmitted")
        latest = ManagementNotification.objects.create(category="payments", source_key=f"sla:payment:{self.payment.pk}", title="Overdue")
        response = self.client.get(self.url, {"category": "payments"})
        self.assertEqual(response.context["notification_counts"]["action"], 1)
        items = response.context["overdue_notifications"] + response.context["upcoming_notifications"]
        self.assertEqual([item.pk for item in items], [latest.pk])
        self.assertEqual(ManagementNotification.objects.filter(category="payments").count(), 3)
        self.assertTrue(items[0].can_review_payment)
        archive = self.client.get(self.url, {"category": "payments", "view": "archive"})
        self.assertEqual(archive.context["notification_counts"]["archive"], 2)
        self.assertContains(archive, "سابقه؛ مورد جدیدتری در صف است")
        self.assertNotContains(archive, f"/notifications/{self.alert.pk}/payment/approve/")

    def test_return_link_keeps_filter_page_and_row_and_rejects_external_return(self):
        back = self.url + f"?category=payments&view=action&page=2#notification-{self.alert.pk}"
        response = self.open(self.alert, **{"return": back})
        self.assertEqual(parse_qs(urlsplit(response.url).query)["inbox_return"], [back])
        detail = self.client.get(response.url)
        self.assertContains(detail, "بازگشت به صندوق کار")
        self.assertEqual(detail.context["inbox_return_url"], back)
        for unsafe in ("//evil.test/fa/management/notifications/", "https://evil.test/", "/fa/management/customers/"):
            self.assertEqual(safe_inbox_return(unsafe), "")

    def test_english_redirect_localizes_stored_persian_path(self):
        response = self.client.get(f"/en/management/notifications/{self.alert.pk}/open/")
        self.assertTrue(response.url.startswith("/en/management/approvals/?payment="))
        page = self.client.get("/en/management/notifications/", {"category": "payments"})
        self.assertContains(page, "Order amount")
        self.assertNotContains(page, "مبلغ سفارش")

    def test_support_opens_only_the_named_ticket(self):
        ticket = SupportTicket.objects.create(user=self.buyer, subject="Specific ticket", message="Test", category="technical")
        item = ManagementNotification.objects.get(source_key=f"support:{ticket.pk}")
        self.assertEqual(self.open(item).url, reverse("management_portal:assessment_support") + f"?ticket={ticket.pk}")

    def test_contract_review_opens_the_actual_contract_not_a_generic_case(self):
        proposal = ContractProposal.objects.create(customer_name="Synthetic contract", customer_phone="989120000001", project_title="Test", project_scope="Test", amount_irr=100000, delivery_terms="Test", created_by=self.admin)
        version = ContractVersion.objects.create(proposal=proposal, number=1, snapshot={}, snapshot_hash="test", created_by=self.admin)
        review = ContractReview.objects.create(version=version)
        alert = ManagementNotification.objects.get(source_key=f"contract-review:{review.pk}")
        ManagementNotification.objects.filter(pk=alert.pk).update(target_url=reverse("management_portal:workspace_list"))
        self.assertEqual(self.open(alert).url, reverse("management_portal:contract_detail", args=[proposal.pk]))

    def test_pagination_has_no_hidden_cutoff_and_keeps_filters(self):
        for index in range(35):
            ManagementNotification.objects.create(category="support", source_key=f"pagination:{index}", title=f"Work {index}", target_url=reverse("management_portal:assessment_support"))
        response = self.client.get(self.url, {"category": "support", "page": 2})
        self.assertEqual(response.context["inbox_page"].paginator.count, 35)
        self.assertEqual(len(response.context["inbox_page"]), 5)
        self.assertContains(response, "category=support")
        self.assertContains(response, 'name="next"')

    def test_receipt_presentation_is_batched(self):
        items = [self.alert]
        with self.assertNumQueries(1):
            present_sources(items, self.admin, "fa")
        items *= 15
        with self.assertNumQueries(1):
            present_sources(items, self.admin, "fa")

    def test_view_without_change_permission_has_no_payment_decision(self):
        staff = User.objects.create_user(username="inbox-viewer", email="inbox-viewer@example.test", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(content_type__app_label="assessments", codename="view_manualpaymentsubmission"))
        self.alert.owner = staff
        self.alert.save(update_fields=["owner"])
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertContains(response, "INBOX-REF-1")
        self.assertNotContains(response, f"/notifications/{self.alert.pk}/payment/approve/")
        result = self.client.post(reverse("management_portal:notification_payment_action", args=[self.alert.pk, "approve"]))
        self.assertEqual(result.status_code, 403)

    def test_csrf_and_visibility_deny_mutation(self):
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.admin)
        url = reverse("management_portal:notification_payment_action", args=[self.alert.pk, "approve"])
        self.assertEqual(csrf.post(url).status_code, 403)
        staff = User.objects.create_user(username="inbox-outsider", email="inbox-outsider@example.test", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "pending")

    def test_snooze_remains_per_viewer_and_not_resolved(self):
        other = User.objects.create_superuser(username="inbox-other", email="inbox-other@example.test", password="test-safe")
        NotificationReceipt.objects.create(user=other, notification=self.alert)
        before = timezone.now()
        response = self.client.post(reverse("management_portal:notification_snooze", args=[self.alert.pk]), {"duration": "1h"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        own = NotificationReceipt.objects.get(user=self.admin, notification=self.alert)
        self.assertGreaterEqual(own.snoozed_until, before + timedelta(hours=1))
        self.assertIn(timezone.localtime(own.snoozed_until).strftime("%H:%M"), response.json()["message"])
        self.assertIsNone(own.seen_at)
        self.assertIsNone(NotificationReceipt.objects.get(user=other, notification=self.alert).snoozed_until)
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, "unread")

    def test_live_feed_reconciles_existing_resolved_rows_and_hides_other_roles(self):
        ManagementNotification.objects.filter(pk=self.alert.pk).update(status="resolved")
        response = self.client.get(reverse("management_portal:notification_feed"), {"since": self.alert.pk, "inbox_ids": f"{self.alert.pk},invalid,{'9'*100}"})
        states = response.json()["inbox_states"]
        self.assertEqual(len(states), 1)
        self.assertTrue(states[0]["inactive"])
        self.assertEqual(response["Cache-Control"], "no-store, private")
        staff = User.objects.create_user(username="feed-outsider", email="feed-outsider@example.test", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("management_portal:notification_feed"), {"inbox_ids": self.alert.pk}).json()["inbox_states"], [])

    def test_claim_replay_does_not_duplicate_audit_and_bad_assignee_is_recoverable(self):
        url = reverse("management_portal:notification_claim", args=[self.alert.pk])
        for _ in range(2):
            self.assertEqual(self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code, 200)
        self.assertEqual(OperationalAudit.objects.filter(action="notification_claimed", target_id=str(self.alert.pk)).count(), 1)
        response = self.client.post(reverse("management_portal:notification_assign", args=[self.alert.pk]), {"user_id": "not-a-number"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 400)

    def test_personal_archive_is_not_global_resolution(self):
        event = ManagementNotification.objects.create(category="sales", title="Update", source_key="inbox:archive", requires_action=False, target_url=self.url)
        response = self.client.post(reverse("management_portal:notification_status", args=[event.pk, "read"]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.json()["display_status"], "بایگانی برای من")
        event.refresh_from_db()
        self.assertEqual(event.status, "unread")

    def test_auto_approval_keeps_legacy_contact_destination_without_receipt_permission(self):
        customer_id = CustomerContact.objects.get(user=self.buyer).customer_id
        CustomerContact.objects.filter(user=self.buyer).update(is_primary=True)
        CustomerContact.objects.create(
            customer=Customer.objects.create(name="Secondary customer"),
            user=self.buyer, name="Secondary contact", is_primary=False,
        )
        Order.objects.filter(pk=self.order.pk).update(customer=None)
        staff = User.objects.create_user(username="auto-reviewer", email="auto-reviewer@example.test", is_staff=True)
        alert = ManagementNotification.objects.create(category="payments", title="Access granted", source_key=f"payment-auto-approved:{self.payment.pk}", owner=staff, requires_action=False)
        self.client.force_login(staff)
        self.assertEqual(self.open(alert).url, reverse("management_portal:customer_assessment_detail", args=[customer_id, self.buyer.pk]))
        page = self.client.get(self.url, {"view": "events"})
        self.assertNotContains(page, "INBOX-REF-1")
        self.assertNotContains(page, "2,000,000")


@skipUnless(connection.vendor == "postgresql", "Real PostgreSQL row locks required")
class InboxPaymentConcurrencyTests(TransactionTestCase):
    def test_two_simultaneous_claims_record_one_assignment(self):
        root = User.objects.create_superuser(username="claim-race", email="claim-race@example.test", password="test-safe")
        alert = ManagementNotification.objects.create(category="sales", title="Synthetic work", source_key="inbox:claim-race")
        gate = Barrier(2)

        def claim():
            close_old_connections()
            try:
                with translation.override("fa"):
                    client = Client()
                    client.force_login(root)
                    gate.wait(timeout=10)
                    return client.post(reverse("management_portal:notification_claim", args=[alert.pk]), HTTP_X_REQUESTED_WITH="XMLHttpRequest").status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(claim) for _ in range(2)]
            self.assertEqual([future.result(timeout=30) for future in futures], [200, 200])
        alert.refresh_from_db()
        self.assertEqual(alert.owner, root)
        self.assertEqual(OperationalAudit.objects.filter(action="notification_claimed", target_id=str(alert.pk)).count(), 1)

    def test_two_simultaneous_decisions_grant_access_only_once(self):
        root = User.objects.create_superuser(username="inbox-race", email="inbox-race@example.test", password="test-safe")
        buyer = User.objects.create_user(username="inbox-race-buyer", email="race-buyer@example.test")
        exam = Exam.objects.create(slug="inbox-race", title_fa="آزمون", title_en="Exam", language_mode="bilingual")
        order = Order.objects.create(user=buyer, exam=exam, amount_irr=2000000, gateway="card_transfer", terms_version="v1", terms_accepted_at=timezone.now())
        payment = ManualPaymentSubmission.objects.create(order=order, payer_name="Synthetic", reference_number="INBOX-RACE", paid_at=timezone.now())
        alert = ManagementNotification.objects.get(source_key=f"payment:{payment.pk}")
        gate = Barrier(2)

        def decide():
            close_old_connections()
            try:
                with translation.override("fa"):
                    client = Client()
                    client.force_login(root)
                    gate.wait(timeout=10)
                    response = client.post(reverse("management_portal:notification_payment_action", args=[alert.pk, "approve"]), HTTP_X_REQUESTED_WITH="XMLHttpRequest")
                    return response.status_code, response.json()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(decide) for _ in range(2)]
            outcomes = [future.result(timeout=30) for future in futures]
        self.assertEqual(sorted(status for status, _ in outcomes), [200, 409], outcomes)
        self.assertEqual(ExamEntitlement.objects.filter(order=order).count(), 1)
        self.assertEqual(PaymentTransaction.objects.filter(order=order, status="verified").count(), 1)
        self.assertEqual(OperationalAudit.objects.filter(action="notification_payment_approve", target_id=str(payment.pk)).count(), 1)
