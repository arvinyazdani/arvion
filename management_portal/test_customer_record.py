from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone, translation
from django.test.utils import CaptureQueriesContext
from django.db import connection

from accounts.models import User
from assessments.models import Exam, ExamVersion, ExamEntitlement, Attempt, AttemptResult, Order, ManualPaymentSubmission
from .models import Customer, CustomerContact, CustomerCase, CustomerEvent, CaseDocument, CaseActivity, CaseTask, OperationalAudit


class CustomerRecordTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.admin = User.objects.create_superuser(username="record-admin", email="record-admin@example.test", password="safe-test")
        self.buyer = User.objects.create_user(username="record-buyer", email="record-buyer@example.test", mobile="09120004321")
        self.customer = Customer.objects.create(name="شرکت نمونه", phone=self.buyer.mobile)
        CustomerContact.objects.create(customer=self.customer, name="مدیر نمونه", user=self.buyer, phone=self.buyer.mobile)
        self.exam = Exam.objects.create(slug="record-test", title_fa="آزمون نمونه", title_en="Sample exam", language_mode="bilingual")
        self.order = Order.objects.create(customer=self.customer, user=self.buyer, exam=self.exam, amount_irr=2000000)
        self.payment = ManualPaymentSubmission.objects.create(order=self.order, payer_name="Sample payer", reference_number="RECORD-QA", paid_at=timezone.now())
        self.url = reverse("management_portal:customer_detail", args=[self.customer.pk])
        self.client.force_login(self.admin)

    def test_exact_payment_and_order_destinations(self):
        response = self.client.get(self.url)
        self.assertContains(response, f'?payment={self.payment.pk}#payment-{self.payment.pk}')
        self.assertContains(response, f'#order-{self.order.pk}')
        self.assertContains(response, 'customer-record.js')
        self.assertEqual(len(response.context["record_pages"]), 4)

    def test_seen_record_is_read_only_and_documents_preserved(self):
        case = CustomerCase.objects.create(customer=self.customer, kind="crm", customer_name=self.customer.name)
        document = CaseDocument.objects.create(case=case, kind="initial", title="QA document", snapshot={"answer": "saved"})
        counts = [model.objects.count() for model in (CustomerEvent, CaseActivity, CaseTask, OperationalAudit, CaseDocument)]
        self.client.get(self.url)
        self.assertEqual(counts, [model.objects.count() for model in (CustomerEvent, CaseActivity, CaseTask, OperationalAudit, CaseDocument)])
        document.refresh_from_db()
        self.assertEqual(document.snapshot, {"answer": "saved"})

    def test_history_is_paginated_filtered_and_has_actor(self):
        CustomerEvent.objects.bulk_create([CustomerEvent(customer=self.customer, category="system", event_type="qa", title_fa=f"رویداد {n}", title_en=f"Event {n}", actor=self.admin) for n in range(34)])
        response = self.client.get(self.url, {"event_kind": "system", "events_page": 2})
        self.assertEqual(response.context["event_page"].paginator.count, 34)
        self.assertEqual(len(response.context["events"]), 15)
        self.assertContains(response, "event_kind=system")
        self.assertContains(response, self.admin.email)
        self.assertEqual(self.client.get(self.url, {"events_page": "nonsense"}).status_code, 200)

    def test_malformed_and_foreign_event_sources_are_not_links(self):
        foreign = Customer.objects.create(name="Unrelated")
        foreign_user = User.objects.create_user(username="record-other", email="other@example.test")
        order = Order.objects.create(customer=foreign, user=foreign_user, exam=self.exam, amount_irr=2000000)
        payment = ManualPaymentSubmission.objects.create(order=order, payer_name="Other", reference_number="OTHER", paid_at=timezone.now())
        for kind, source_id in (("assessments.attempt", "broken-uuid"), ("assessments.order", str(order.pk)), ("assessments.manualpaymentsubmission", str(payment.pk))):
            CustomerEvent.objects.create(customer=self.customer, category="system", event_type="qa", title_fa="نامعتبر", title_en="Invalid", source_type=kind, source_id=source_id)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f"?payment={payment.pk}")
        self.assertNotContains(response, f"#order-{order.pk}")

    def test_view_only_staff_does_not_see_forbidden_actions(self):
        viewer = User.objects.create_user(username="record-viewer", email="viewer@example.test", is_staff=True)
        self.client.force_login(viewer)
        response = self.client.get(self.url)
        self.assertNotContains(response, f'/customers/{self.customer.pk}/message/')
        self.assertNotContains(response, f'/customers/{self.customer.pk}/tasks/new/')
        self.assertNotContains(response, f'?payment={self.payment.pk}')
        self.assertNotContains(response, '/management/contracts/new/')
        self.assertEqual(self.client.post(reverse("management_portal:customer_task_create", args=[self.customer.pk]), {"title": "Denied", "priority": "normal"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("management_portal:customer_message_send", args=[self.customer.pk]), {"recipient": self.buyer.mobile, "message": "Denied", "confirm": "on"}).status_code, 403)
        self.assertFalse(CaseTask.objects.exists())

    def test_contact_permission_is_unchanged_and_is_audited(self):
        viewer = User.objects.create_user(username="contact-staff", email="contact-staff@example.test", is_staff=True)
        self.client.force_login(viewer)
        response = self.client.post(reverse("management_portal:customer_contact_create", args=[self.customer.pk]), {"name": "New contact"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(OperationalAudit.objects.filter(action="customer_contact_created", target_id=str(self.customer.pk)).exists())

    def test_anonymous_nonstaff_and_csrf_cannot_write(self):
        path = reverse("management_portal:customer_activity_create", args=[self.customer.pk])
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(self.url).status_code, 302)
        self.assertEqual(self.client.post(path, {"title": "Denied"}).status_code, 302)
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(path, {"title": "Denied"}).status_code, 403)
        self.assertFalse(CaseActivity.objects.filter(title="Denied").exists())

    def test_export_has_safe_return_to_record_without_changing_download(self):
        case = CustomerCase.objects.create(customer=self.customer, kind="crm", customer_name=self.customer.name)
        path = reverse("management_portal:crm_case_export", args=[case.pk])
        response = self.client.get(path, {"customer_record": self.customer.pk})
        self.assertEqual(response.context["back_url"], self.url + "#customer-documents")
        response = self.client.get(path, {"customer_record": "https://evil.invalid"})
        self.assertEqual(response.context["back_url"], reverse("management_portal:crm_case_detail", args=[case.pk]))
        self.assertIn("attachment;", self.client.get(path, {"download": "1"})["Content-Disposition"])

    def test_english_system_labels_and_exam_title(self):
        response = self.client.get(f"/en/management/customers/{self.customer.pk}/")
        self.assertContains(response, "New action")
        self.assertContains(response, "Sample exam")
        self.assertNotContains(response, "سفارش آزمون ثبت شد")
        self.assertNotContains(response, "آزمون نمونه")

    def test_old_paid_order_state_survives_pagination(self):
        Order.objects.filter(pk=self.order.pk).update(status="paid")
        exams = [Exam.objects.create(slug=f"history-{n}", title_fa="سابقه", title_en="History", language_mode="bilingual") for n in range(32)]
        Order.objects.bulk_create([Order(user=self.buyer, customer=self.customer, exam=exam, amount_irr=2000000) for exam in exams])
        response = self.client.get(self.url)
        self.assertEqual(response.context["record_pages"]["orders"].paginator.count, 33)
        self.assertEqual(response.context["journey"].key, "ready")
        self.assertEqual(len(response.context["orders"]), 15)

    def test_record_queries_do_not_grow_per_case_contact_order(self):
        self.client.get(self.url)  # warm auth/content-type caches
        with CaptureQueriesContext(connection) as initial:
            self.client.get(self.url)
        for n in range(7):
            CustomerCase.objects.create(customer=self.customer, kind="general", customer_name=f"Case {n}")
            CustomerContact.objects.create(customer=self.customer, name=f"Contact {n}", user=self.buyer)
            exam = Exam.objects.create(slug=f"query-{n}", title_fa="آزمون", title_en="Exam", language_mode="bilingual")
            Order.objects.create(customer=self.customer, user=self.buyer, exam=exam, amount_irr=2000000)
        with CaptureQueriesContext(connection) as expanded:
            self.client.get(self.url)
        self.assertLessEqual(len(expanded), len(initial) + 1)

    def test_pending_receipt_remains_actionable_after_newer_unpaid_order(self):
        exam = Exam.objects.create(slug="newer-unpaid", title_fa="جدید", title_en="New", language_mode="bilingual")
        Order.objects.create(customer=self.customer, user=self.buyer, exam=exam, amount_irr=2000000)
        response = self.client.get(self.url)
        self.assertEqual(response.context["journey"].key, "payment_pending")
        self.assertTrue(any(f"?payment={self.payment.pk}" in action.url for action in response.context["record_actions"]))

    def test_result_event_opens_exact_attempt(self):
        version = ExamVersion.objects.create(exam=self.exam, version=1)
        entitlement = ExamEntitlement.objects.create(exam=self.exam, order=self.order, user=self.buyer)
        attempt = Attempt.objects.create(exam=self.exam, user=self.buyer, entitlement=entitlement, version=version, status="completed")
        AttemptResult.objects.create(attempt=attempt, percentage=85, level_code="B2", level_title_fa="متوسط", level_title_en="Intermediate", summary_fa="نمونه", summary_en="Sample")
        response = self.client.get(self.url)
        result_event = next(event for event in response.context["events"] if event["title"] == "نتیجه آزمون آماده شد")
        self.assertEqual(result_event["url"], reverse("management_portal:customer_assessment_detail", args=[self.customer.pk, self.buyer.pk]) + f"?attempt={attempt.pk}#attempt-{attempt.pk}")
        self.assertContains(self.client.get(result_event["url"]), f'id="attempt-{attempt.pk}"')
        CustomerEvent.objects.create(customer=self.customer, category="assessment", event_type="qa", title_fa="شروع", title_en="Started", description=self.exam.title_fa, source_type="assessments.attempt", source_id=str(attempt.pk))
        english = self.client.get(f"/en/management/customers/{self.customer.pk}/")
        self.assertNotContains(english, self.exam.title_fa)
        self.assertContains(english, self.exam.title_en)

    def test_form_ids_are_unique_and_account_menu_deduplicated(self):
        CustomerContact.objects.create(customer=self.customer, user=self.buyer, name="Second contact")
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["account_contacts"]), 1)
        for field_id in ("task_title", "activity_title", "contact_name", "message_recipient"):
            self.assertContains(response, f'id="{field_id}"', count=1)

    def test_legacy_activity_payment_metadata_and_malformed_type(self):
        from django.contrib.contenttypes.models import ContentType
        case = CustomerCase.objects.filter(customer=self.customer).first()
        activity = CaseActivity.objects.create(case=case, kind="system", title="Receipt legacy", metadata={"content_type": ContentType.objects.get_for_model(self.payment).pk, "object_id": self.payment.pk})
        CaseActivity.objects.create(case=case, kind="note", title="Malformed", metadata={"content_type": {"bad": True}})
        response = self.client.get(self.url)
        event = next(item for item in response.context["events"] if item["title"] == activity.title)
        self.assertEqual(event["url"], reverse("management_portal:approvals") + f"?payment={self.payment.pk}#payment-{self.payment.pk}")
