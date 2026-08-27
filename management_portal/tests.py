from django.contrib.auth.models import Permission
from datetime import timedelta
import json
from pathlib import Path
from django.test import TestCase, override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import User
from accounts.staff_roles import group_name
from crm_orders.models import CrmOrder, CrmSpecialistDiscovery
from assessments.models import Attempt, AttemptResult, Exam, ExamEntitlement, ExamVersion, IntegrityEvent, ManualPaymentSubmission, Order, PaymentTransaction, SupportTicket
from contracts.models import ContractProposal
from leads.models import Lead
from management_portal.models import CaseActivity, CaseTask, Customer, CustomerCase, CustomerContact, CustomerEvent, ManagementNotification, NotificationReceipt, OperationalAudit, PushSubscription, SavedCustomerSegment, SMSCampaign, SMSDispatch, SMSMessageTemplate, StaffAccessAudit, SystemLog
from management_portal.notifications import process_notifications
from services.models import Service
from core.sms.backends import SMSResult
from unittest.mock import patch


class ManagementDashboardTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.url = reverse("management_portal:dashboard")

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_non_staff_user_is_redirected(self):
        user = User.objects.create_user(username="client", email="client@example.com", password="safe-password")
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_staff_sees_device_push_onboarding_across_public_web_app(self):
        user = User.objects.create_user(username="staff-push", email="staff-push@example.com", password="safe-password", is_staff=True)
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "core/js/staff-push.js")
        self.assertContains(response, "RVION_STAFF_PUSH")

    def test_staff_only_sees_permitted_operational_data(self):
        user = User.objects.create_user(username="sales", email="sales@example.com", password="safe-password", is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename="view_crmorder"), Permission.objects.get(codename="change_crmorder"))
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "نیازسنجی CRM")
        self.assertNotContains(response, "پرداخت منتظر بررسی")
        self.assertNotContains(response, "حساب نیازمند تأیید")

    def test_sales_staff_can_manage_requests_without_django_admin_links(self):
        user = User.objects.create_user(username="sales-v2", email="sales-v2@example.com", password="safe-password", is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename="view_crmorder"), Permission.objects.get(codename="change_crmorder"))
        order = CrmOrder.objects.create(
            organization_name="سازمان آزمایشی", industry="فناوری", organization_size="under_10", contact_name="مینا",
            job_title="مدیر", work_email="mina@example.com", phone="09120000000", crm_user_count="1_5",
            current_process="فرآیند فعلی سازمان آزمایشی", main_pain_points="نبود پیگیری یکپارچه", success_metrics="پاسخ سریع",
            critical_workflows="پیگیری فروش مرحله به مرحله", reports_needed="", permission_requirements="", hosting_preference="cloud",
            budget_range="estimate", expected_timeline="unsure", decision_process="تصمیم مدیرعامل پس از بررسی", privacy_accepted_at=timezone.now(),
        )
        self.client.force_login(user)
        listing = self.client.get(reverse("management_portal:request_list"))
        self.assertContains(listing, "سازمان آزمایشی")
        self.assertNotContains(listing, 'href="/admin/')
        detail = self.client.get(reverse("management_portal:request_detail", args=["crm", order.pk]))
        self.assertContains(detail, "نبود پیگیری یکپارچه")
        self.assertContains(detail, "آماده‌سازی و ارسال مشتری")
        export = self.client.get(reverse("management_portal:request_export", args=["crm", order.pk]))
        self.assertEqual(export.status_code, 200)
        self.assertIn("گزارش کامل نیازسنجی CRM", export.content.decode("utf-8"))
        self.assertNotIn("Content-Disposition", export)
        self.assertContains(export, "پیش‌نمایش امن داخل برنامه")
        self.assertFalse(OperationalAudit.objects.filter(action="request_exported", target_id=str(order.pk)).exists())
        download = self.client.get(reverse("management_portal:request_export", args=["crm", order.pk]) + "?download=1")
        self.assertEqual(download["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("attachment;", download["Content-Disposition"])
        self.assertEqual(OperationalAudit.objects.filter(action="request_exported", target_id=str(order.pk)).count(), 1)
        case = CustomerCase.objects.get(source_object_id=order.pk, kind="crm")
        workspace = self.client.get(reverse("management_portal:crm_workspace"))
        self.assertContains(workspace, "سازمان آزمایشی")
        self.assertContains(self.client.get(reverse("management_portal:crm_case_detail", args=[case.pk])), case.code)
        self.client.post(reverse("management_portal:crm_task_create", args=[case.pk]), {"title": "تماس پیگیری", "priority": "high"})
        self.assertTrue(CaseTask.objects.filter(case=case, title="تماس پیگیری").exists())
        case_preview = self.client.get(reverse("management_portal:crm_case_export", args=[case.pk]))
        self.assertEqual(case_preview.status_code, 200)
        self.assertNotIn("Content-Disposition", case_preview)
        self.assertFalse(OperationalAudit.objects.filter(action="crm_case_exported", target_id=str(case.pk)).exists())
        case_download = self.client.get(reverse("management_portal:crm_case_export", args=[case.pk]) + "?download=1")
        self.assertIn("attachment;", case_download["Content-Disposition"])
        self.assertEqual(OperationalAudit.objects.filter(action="crm_case_exported", target_id=str(case.pk)).count(), 1)
        discovery = CrmSpecialistDiscovery.objects.create(order=order, status="submitted", answers={"workflow": "ok"})
        self.assertTrue(ManagementNotification.objects.filter(source_key=f"crm-specialist:{discovery.pk}:submitted").exists())

    def test_all_staff_can_open_unified_customer_workspace_and_contacts(self):
        staff = User.objects.create_user(username="operations", email="operations@example.com", password="safe-password", is_staff=True)
        account = User.objects.create_user(username="customer-account", email="customer@example.com", mobile="09120000001", password="safe-password")
        customer = Customer.objects.create(name="شرکت یکپارچه", phone="09120000001", email="customer@example.com")
        CustomerContact.objects.create(customer=customer, name="مینا رضایی", role="مدیر پروژه", phone="09120000001", email="customer@example.com", user=account, is_primary=True)
        case = CustomerCase.objects.create(customer=customer, kind="crm", customer_name="شرکت یکپارچه", contact_name="مینا رضایی", phone="09120000001", email="customer@example.com")
        self.client.force_login(staff)
        listing = self.client.get(reverse("management_portal:customer_workspace"))
        self.assertContains(listing, "شرکت یکپارچه")
        detail = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(detail, "مینا رضایی")
        self.assertContains(detail, "حساب سایت متصل")
        self.assertContains(detail, case.code)

    def test_customer_workspace_surfaces_data_quality_without_changing_records(self):
        staff = User.objects.create_user(username="quality-staff", email="quality-staff@example.com", password="safe-password", is_staff=True)
        Customer.objects.create(name="بدون مخاطب", phone="09120007777")
        Customer.objects.create(name="تکراری اول", email="same@example.com")
        Customer.objects.create(name="تکراری دوم", email="same@example.com")
        self.client.force_login(staff)
        response = self.client.get(reverse("management_portal:customer_workspace"))
        self.assertContains(response, "کنترل کیفیت داده")
        self.assertContains(response, "مشتری بدون مخاطب")
        self.assertContains(response, "same@example.com")
        self.assertEqual(Customer.objects.count(), 3)

    def test_duplicate_review_compares_records_without_merging_them(self):
        staff = User.objects.create_user(username="duplicate-staff", email="duplicate-staff@example.com", password="safe-password", is_staff=True)
        first = Customer.objects.create(name="شرکت اول", phone="09120008888")
        second = Customer.objects.create(name="شرکت دوم", phone="09120008888")
        self.client.force_login(staff)
        response = self.client.get(reverse("management_portal:customer_duplicates"), {"field": "phone", "value": "09120008888"})
        self.assertContains(response, "پیش از ادغام، پرونده‌ها را کنار هم ببینید")
        self.assertContains(response, first.name)
        self.assertContains(response, second.name)
        self.assertEqual(Customer.objects.filter(phone="09120008888").count(), 2)

    def test_superuser_can_merge_only_confirmed_duplicate_records_with_audit(self):
        root = User.objects.create_superuser(username="merge-root", email="merge-root@example.com", password="safe-password")
        target = Customer.objects.create(name="پرونده مرجع", phone="09120009999")
        source = Customer.objects.create(name="پرونده تکراری", phone="09120009999")
        case = CustomerCase.objects.create(customer=source, kind="crm", customer_name=source.name, phone=source.phone)
        CustomerContact.objects.create(customer=source, name="مخاطب", phone="09120009999", is_primary=True)
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:customer_merge", args=[source.pk]), {"target_id": target.pk, "confirmation": "MERGE"})
        self.assertRedirects(response, reverse("management_portal:customer_detail", args=[target.pk]))
        self.assertFalse(Customer.objects.filter(pk=source.pk).exists())
        case.refresh_from_db()
        self.assertEqual(case.customer_id, target.pk)
        self.assertTrue(CustomerContact.objects.filter(customer=target, name="مخاطب").exists())
        self.assertTrue(OperationalAudit.objects.filter(action="customer_merged", target_id=str(target.pk)).exists())

    def test_customer_record_collects_linked_contract_and_order(self):
        root = User.objects.create_superuser(username="customer-root", email="customer-root@example.com", password="safe-password")
        customer_user = User.objects.create_user(username="customer-finance", email="finance@example.com", password="safe-password")
        customer = Customer.objects.create(name="مشتری مالی", phone="09120000002", email="finance@example.com")
        CustomerContact.objects.create(customer=customer, name="مدیر مالی", phone="09120000002", email="finance@example.com", user=customer_user, is_primary=True)
        exam = Exam.objects.create(slug="customer-link-exam", title_fa="آزمون مالی", title_en="Finance test", description_fa="", description_en="", language_mode="bilingual")
        Order.objects.create(user=customer_user, customer=customer, exam=exam, amount_irr=500_000, status="paid")
        ContractProposal.objects.create(customer=customer, customer_name="مشتری مالی", customer_phone="09120000002", customer_email="finance@example.com", project_title="پروژه مالی", project_scope="دامنه", amount_irr=1_000_000, delivery_terms="دو هفته", created_by=root)
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(response, "پروژه مالی")
        self.assertContains(response, "آزمون مالی")

    def test_registered_account_without_order_opens_as_customer_followup_record(self):
        root = User.objects.create_superuser(username="journey-root", email="journey-root@example.com", password="safe-password")
        account = User.objects.create_user(username="journey-client", email="journey@example.com", mobile="989120001234", password="safe-password", is_active=True)
        self.client.force_login(root)
        dashboard = self.client.get(reverse("management_portal:dashboard"))
        self.assertContains(dashboard, "عضو شده، بدون سفارش")
        self.assertContains(dashboard, account.mobile)
        opened = self.client.get(reverse("management_portal:customer_account_open", args=[account.pk]))
        customer = CustomerContact.objects.get(user=account).customer
        self.assertRedirects(opened, reverse("management_portal:customer_detail", args=[customer.pk]))
        detail = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(detail, "دعوت به ثبت سفارش")

    def test_customer_journey_is_derived_from_current_domain_state(self):
        root = User.objects.create_superuser(username="state-root", email="state-root@example.com", password="safe-password")
        account = User.objects.create_user(username="state-client", email="state-client@example.com", mobile="989120007777", password="safe-password", is_active=True)
        customer = Customer.objects.create(name="مشتری وضعیت", phone=account.mobile, email=account.email)
        CustomerContact.objects.create(customer=customer, user=account, name=customer.name, phone=account.mobile, is_primary=True)
        exam = Exam.objects.create(slug="state-exam", title_fa="آزمون وضعیت", title_en="State exam", description_fa="", description_en="", language_mode="bilingual")
        self.client.force_login(root)

        registered = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(registered, "عضو شده؛ هنوز سفارشی ندارد")
        order = Order.objects.create(user=account, customer=customer, exam=exam, amount_irr=1_200_000, status="pending")
        pending = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(pending, "سفارش ثبت شده؛ پرداخت انجام نشده")
        order.status = "paid"
        order.paid_at = timezone.now()
        order.save(update_fields=("status", "paid_at", "updated_at"))
        ready = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(ready, "دسترسی فعال؛ آزمون شروع نشده")

    def test_customer_events_form_one_deduplicated_timeline(self):
        root = User.objects.create_superuser(username="event-root", email="event-root@example.com", password="safe-password")
        account = User.objects.create_user(username="event-client", email="event-client@example.com", mobile="09120004567", password="safe-password", is_active=True)
        customer = Customer.objects.create(name="مشتری رویداد", phone=account.mobile, email=account.email)
        CustomerContact.objects.create(customer=customer, user=account, name=customer.name, phone=account.mobile, is_primary=True)
        exam = Exam.objects.create(slug="event-exam", title_fa="آزمون رویداد", title_en="Event assessment", description_fa="", description_en="", language_mode="bilingual")
        order = Order.objects.create(user=account, customer=customer, exam=exam, amount_irr=1_000_000)
        order.save()
        self.assertEqual(CustomerEvent.objects.filter(customer=customer, event_type="order_created").count(), 1)
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(response, "سفارش آزمون ثبت شد", count=1)

    def test_staff_can_save_reuse_and_delete_own_customer_segment(self):
        staff = User.objects.create_user(username="segment-owner", email="segment-owner@example.com", password="safe-password", is_staff=True)
        old_customer = Customer.objects.create(name="قدیمی")
        Customer.objects.filter(pk=old_customer.pk).update(updated_at=timezone.now() - timedelta(days=40))
        self.client.force_login(staff)
        saved = self.client.post(reverse("management_portal:customer_workspace"), {
            "segment_name": "پیگیری قدیمی", "inactive_days": "30",
        })
        segment = SavedCustomerSegment.objects.get(owner=staff)
        self.assertRedirects(saved, reverse("management_portal:customer_workspace") + f"?segment={segment.pk}")
        response = self.client.get(reverse("management_portal:customer_workspace") + f"?segment={segment.pk}")
        self.assertContains(response, "پیگیری قدیمی")
        self.assertContains(response, "قدیمی")
        deleted = self.client.post(reverse("management_portal:customer_segment_delete", args=[segment.pk]))
        self.assertRedirects(deleted, reverse("management_portal:customer_workspace"))
        self.assertFalse(SavedCustomerSegment.objects.filter(pk=segment.pk).exists())

    def test_customer_funnel_reports_conversion_and_bottlenecks_from_live_data(self):
        root = User.objects.create_superuser(username="report-root", email="report-root@example.com", password="safe-password")
        exam = Exam.objects.create(slug="report-exam", title_fa="آزمون گزارش", title_en="Report assessment", description_fa="", description_en="", language_mode="bilingual")
        for index, status in enumerate((None, "pending", "paid"), start=1):
            user = User.objects.create_user(username=f"report-user-{index}", email=f"report-{index}@example.com", mobile=f"0912000100{index}", password="safe-password", is_active=True)
            customer = Customer.objects.create(name=f"مشتری {index}", phone=user.mobile)
            CustomerContact.objects.create(customer=customer, user=user, name=customer.name, phone=user.mobile, is_primary=True)
            if status:
                Order.objects.create(user=user, customer=customer, exam=exam, amount_irr=1_000_000, status=status, paid_at=timezone.now() if status == "paid" else None)
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:customer_reports"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "قیف تبدیل و نقاط توقف مشتریان")
        stages = response.context["report"]["stages"]
        self.assertEqual([stage["count"] for stage in stages[:3]], [3, 2, 1])
        self.assertEqual(stages[1]["dropoff"], 1)

    def test_saved_segment_permissions_are_enforced_server_side(self):
        owner = User.objects.create_user(username="segment-sec-owner", email="segment-sec-owner@example.com", password="safe-password", is_staff=True)
        outsider = User.objects.create_user(username="segment-sec-other", email="segment-sec-other@example.com", password="safe-password", is_staff=True)
        segment = SavedCustomerSegment.objects.create(owner=owner, name="خصوصی", filters={"journey": "registered"})
        self.client.force_login(outsider)
        self.assertEqual(self.client.post(reverse("management_portal:customer_segment_delete", args=[segment.pk])).status_code, 403)
        self.assertTrue(SavedCustomerSegment.objects.filter(pk=segment.pk).exists())
        self.client.force_login(owner)
        self.client.post(reverse("management_portal:customer_workspace"), {"segment_name": "تلاش اشتراک", "journey": "registered", "is_shared": "on"})
        self.assertFalse(SavedCustomerSegment.objects.get(owner=owner, name="تلاش اشتراک").is_shared)

    def test_customer_workspace_stays_paginated_without_n_plus_one_at_scale(self):
        root = User.objects.create_superuser(username="scale-root", email="scale-root@example.com", password="safe-password")
        Customer.objects.bulk_create([Customer(name=f"مشتری حجمی {index}", phone=f"0913{index:07d}") for index in range(1000)], batch_size=250)
        self.client.force_login(root)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("management_portal:customer_workspace"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["customers"]), 30)
        self.assertEqual(response.context["page_obj"].paginator.count, 1000)
        self.assertLessEqual(len(queries), 30)

    def test_customer_reports_and_segments_are_mobile_safe_by_contract(self):
        root = User.objects.create_superuser(username="mobile-report-root", email="mobile-report-root@example.com", password="safe-password")
        self.client.force_login(root)
        reports = self.client.get(reverse("management_portal:customer_reports"))
        workspace = self.client.get(reverse("management_portal:customer_workspace"))
        self.assertContains(reports, "customer-reports.css")
        self.assertContains(workspace, "customer-operations.css")
        report_css = (Path(__file__).parent / "static/management_portal/v2/customer-reports.css").read_text()
        customer_css = (Path(__file__).parent / "static/management_portal/v2/customer-operations.css").read_text()
        self.assertIn("@media(max-width:760px)", report_css)
        self.assertIn("@media(max-width:620px)", customer_css)
        self.assertNotIn("min-width:650px", report_css)

    def test_customer_reports_and_filters_localize_operational_labels(self):
        root = User.objects.create_superuser(username="localized-report-root", email="localized-report@example.com", password="safe-password")
        customer = Customer.objects.create(name="مشتری ترجمه")
        CustomerCase.objects.create(kind="general", customer=customer, customer_name=customer.name, stage="discovery")
        CustomerEvent.objects.create(customer=customer, category="sales", event_type="test", title_fa="پیگیری", title_en="Follow-up")
        self.client.force_login(root)

        english_report = self.client.get("/en/management/customers/reports/")
        english_workspace = self.client.get("/en/management/customers/")
        persian_report = self.client.get("/fa/management/customers/reports/")

        self.assertContains(english_report, "Discovery")
        self.assertNotContains(english_report, ">نیازسنجی<")
        self.assertContains(english_workspace, "Proposal / contract")
        self.assertContains(persian_report, "فروش و پیگیری")

    def test_customer_workspace_surfaces_suspicious_identity_without_hiding_customer(self):
        root = User.objects.create_superuser(username="identity-review-root", email="identity-review@example.com", password="safe-password")
        customer = Customer.objects.create(name="Visit https://example.invalid now")
        self.client.force_login(root)

        response = self.client.get(reverse("management_portal:customer_workspace"))

        self.assertContains(response, "بررسی داده")
        self.assertContains(response, customer.name)
        self.assertContains(response, 'href="#customer-directory"')

    def test_customer_action_center_creates_audited_task_and_activity(self):
        root = User.objects.create_superuser(username="action-root", email="action-root@example.com", password="safe-password")
        customer = Customer.objects.create(name="مشتری عملیات", phone="989120008888")
        self.client.force_login(root)

        task_response = self.client.post(reverse("management_portal:customer_task_create", args=[customer.pk]), {
            "title": "پیگیری شروع آزمون", "description": "تماس تا پایان امروز", "priority": "high",
        })
        activity_response = self.client.post(reverse("management_portal:customer_activity_create", args=[customer.pk]), {
            "kind": "call", "title": "تماس اولیه", "body": "مشتری پاسخ داد",
        })

        self.assertRedirects(task_response, reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-actions")
        self.assertRedirects(activity_response, reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-actions")
        case = customer.cases.get()
        self.assertTrue(case.tasks.filter(title="پیگیری شروع آزمون", created_by=root).exists())
        self.assertTrue(case.activities.filter(kind="call", title="تماس اولیه", actor=root).exists())
        self.assertTrue(OperationalAudit.objects.filter(action="customer_followup_created", target_id=str(customer.pk)).exists())
        self.assertTrue(OperationalAudit.objects.filter(action="customer_activity_logged", target_id=str(customer.pk)).exists())

    def test_english_customer_journey_localizes_system_timeline(self):
        root = User.objects.create_superuser(username="english-state-root", email="english-state-root@example.com", password="safe-password")
        account = User.objects.create_user(username="english-state-client", email="english-state-client@example.com", mobile="989120006666", password="safe-password", is_active=True)
        customer = Customer.objects.create(name="Sample Customer", phone=account.mobile, email=account.email)
        CustomerContact.objects.create(customer=customer, user=account, name=customer.name, phone=account.mobile, is_primary=True)
        exam = Exam.objects.create(slug="english-state-exam", title_fa="آزمون نمونه", title_en="Sample assessment", description_fa="", description_en="", language_mode="bilingual")
        Order.objects.create(user=account, customer=customer, exam=exam, amount_irr=1_200_000, status="paid", paid_at=timezone.now())
        self.client.force_login(root)

        response = self.client.get(f"/en/management/customers/{customer.pk}/")

        self.assertContains(response, "Assessment order created")
        self.assertContains(response, "Payment approved")
        self.assertContains(response, "Sample assessment")
        self.assertNotContains(response, "سفارش آزمون ثبت شد")
        self.assertNotContains(response, "پرداخت تأیید شد")

    def test_view_only_staff_cannot_create_customer_operations(self):
        staff = User.objects.create_user(username="customer-viewer", email="customer-viewer@example.com", password="safe-password", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_crmorder"))
        customer = Customer.objects.create(name="مشتری فقط خواندنی")
        self.client.force_login(staff)

        task = self.client.post(reverse("management_portal:customer_task_create", args=[customer.pk]), {"title": "نباید ساخته شود", "priority": "normal"})
        activity = self.client.post(reverse("management_portal:customer_activity_create", args=[customer.pk]), {"kind": "note", "title": "نباید ثبت شود"})

        self.assertEqual(task.status_code, 403)
        self.assertEqual(activity.status_code, 403)
        self.assertFalse(CustomerCase.objects.filter(customer=customer).exists())

    @patch("management_portal.views.send_sms")
    def test_superuser_can_message_only_a_number_belonging_to_customer(self, mocked_send):
        mocked_send.return_value = SMSResult(provider="test", reference="customer-ref")
        root = User.objects.create_superuser(username="message-root", email="message-root@example.com", password="safe-password")
        customer = Customer.objects.create(name="مشتری پیام", phone="09120004321")
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:customer_message_send", args=[customer.pk]), {
            "recipient": "09120004321", "message": "پیگیری آزمون", "confirm": "on",
        })
        self.assertRedirects(response, reverse("management_portal:customer_detail", args=[customer.pk]) + "#customer-message")
        self.assertTrue(SMSDispatch.objects.filter(recipient="989120004321", status="sent").exists())
        self.assertTrue(OperationalAudit.objects.filter(action="customer_sms_sent", target_id=str(customer.pk)).exists())
        rejected = self.client.post(reverse("management_portal:customer_message_send", args=[customer.pk]), {
            "recipient": "09129999999", "message": "نباید ارسال شود", "confirm": "on",
        })
        self.assertEqual(rejected.status_code, 403)

    def test_customer_assessment_detail_exposes_result_without_answer_key(self):
        root = User.objects.create_superuser(username="result-root", email="result-root@example.com", password="safe-password")
        account = User.objects.create_user(username="result-user", email="result@example.com", mobile="989120005555", password="safe-password")
        customer = Customer.objects.create(name="مشتری نتیجه", phone=account.mobile, email=account.email)
        CustomerContact.objects.create(customer=customer, user=account, name=customer.name, phone=account.mobile, is_primary=True)
        exam = Exam.objects.create(slug="result-exam", title_fa="آزمون نتیجه", title_en="Result exam", description_fa="", description_en="", language_mode="bilingual")
        version = ExamVersion.objects.create(exam=exam, version=1, is_published=True)
        order = Order.objects.create(user=account, customer=customer, exam=exam, amount_irr=1_200_000, status="paid")
        entitlement = ExamEntitlement.objects.create(user=account, exam=exam, order=order)
        attempt = Attempt.objects.create(user=account, exam=exam, version=version, entitlement=entitlement, status="completed", started_at=timezone.now() - timedelta(minutes=20), submitted_at=timezone.now())
        AttemptResult.objects.create(attempt=attempt, correct_count=42, incorrect_count=8, unanswered_count=0, percentage="84.00", level_code="B2", level_title_fa="متوسط رو به بالا", level_title_en="Upper intermediate", summary_fa="خوب", summary_en="Good")
        IntegrityEvent.objects.create(attempt=attempt, event_type="copy")
        self.client.force_login(root)
        detail = self.client.get(reverse("management_portal:customer_detail", args=[customer.pk]))
        self.assertContains(detail, "نتیجه آماده")
        response = self.client.get(reverse("management_portal:customer_assessment_detail", args=[customer.pk, account.pk]))
        self.assertContains(response, "84.00%")
        self.assertContains(response, "B2")
        self.assertContains(response, "فرمان کپی در صفحه سؤال ثبت شد")
        self.assertContains(response, "نتیجه نهایی باید با بررسی انسانی اعلام شود")
        self.assertNotContains(response, "پاسخ صحیح سؤال")

    def test_sales_staff_can_update_request_status_and_internal_note(self):
        user = User.objects.create_user(username="sales-change", email="sales-change@example.com", password="safe-password", is_staff=True)
        user.user_permissions.add(
            Permission.objects.get(codename="view_crmorder"),
            Permission.objects.get(codename="change_crmorder"),
        )
        order = CrmOrder.objects.create(
            organization_name="شرکت پیگیری", industry="خدمات", organization_size="under_10", contact_name="علی",
            job_title="مدیر", work_email="ali@example.com", phone="09120000001", crm_user_count="1_5",
            current_process="ثبت دستی", main_pain_points="پیگیری دشوار", success_metrics="زمان پاسخ",
            critical_workflows="فروش", reports_needed="", permission_requirements="", hosting_preference="cloud",
            budget_range="estimate", expected_timeline="unsure", decision_process="مدیر", privacy_accepted_at=timezone.now(),
        )
        self.client.force_login(user)
        response = self.client.post(reverse("management_portal:request_update", args=["crm", order.pk]), {
            "status": "discovery", "internal_notes": "تماس اولیه انجام شد",
        })
        self.assertRedirects(response, reverse("management_portal:request_detail", args=["crm", order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, "discovery")
        self.assertEqual(order.internal_notes, "تماس اولیه انجام شد")

    def test_view_only_staff_cannot_update_request(self):
        user = User.objects.create_user(username="sales-read", email="sales-read@example.com", password="safe-password", is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename="view_crmorder"))
        order = CrmOrder.objects.create(
            organization_name="شرکت فقط خواندنی", industry="خدمات", organization_size="under_10", contact_name="رضا",
            job_title="مدیر", work_email="reza@example.com", phone="09120000002", crm_user_count="1_5",
            current_process="ثبت دستی", main_pain_points="پیگیری", success_metrics="زمان پاسخ",
            critical_workflows="فروش", reports_needed="", permission_requirements="", hosting_preference="cloud",
            budget_range="estimate", expected_timeline="unsure", decision_process="مدیر", privacy_accepted_at=timezone.now(),
        )
        self.client.force_login(user)
        response = self.client.post(reverse("management_portal:request_update", args=["crm", order.pk]), {"status": "won"})
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, "new")

    def test_superuser_can_approve_customer_account_with_audit(self):
        root = User.objects.create_superuser(username="approval-root", email="approval-root@example.com", password="safe-password")
        customer = User.objects.create_user(username="waiting", email="waiting@example.com", password="safe-password", is_active=False, mobile_verified_at=timezone.now())
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:account_approval", args=[customer.pk, "approve"]))
        self.assertRedirects(response, reverse("management_portal:approvals"))
        customer.refresh_from_db()
        self.assertTrue(customer.is_active)
        self.assertTrue(customer.email_verified)
        self.assertTrue(OperationalAudit.objects.filter(action="account_approve", target_id=str(customer.pk)).exists())

    def test_superuser_approval_overrides_missing_mobile_otp(self):
        root = User.objects.create_superuser(username="approval-safe-root", email="approval-safe-root@example.com", password="safe-password")
        customer = User.objects.create_user(username="waiting-otp", email="waiting-otp@example.com", password="safe-password", is_active=False)
        self.client.force_login(root)

        response = self.client.post(reverse("management_portal:account_approval", args=[customer.pk, "approve"]))

        self.assertRedirects(response, reverse("management_portal:approvals"))
        customer.refresh_from_db()
        self.assertTrue(customer.is_active)
        self.assertTrue(customer.email_verified)
        self.assertIsNotNone(customer.mobile_verified_at)
        self.assertTrue(OperationalAudit.objects.filter(action="account_approve", target_id=str(customer.pk)).exists())

    def test_superuser_can_complete_phone_check_for_temporary_sms_recovery_account(self):
        root = User.objects.create_superuser(username="phone-check-root", email="phone-check-root@example.com", password="safe-password")
        customer = User.objects.create_user(
            username="temporary-phone", email="temporary-phone@example.com", password="safe-password",
            mobile="989120000098", is_active=True,
        )
        self.client.force_login(root)

        queue = self.client.get(reverse("management_portal:approvals"))
        self.assertContains(queue, "فعال موقت · نیازمند تأیید تلفنی")
        self.assertContains(queue, customer.mobile)
        self.assertTrue(ManagementNotification.objects.filter(source_key=f"mobile-verification:{customer.pk}").exists())

        response = self.client.post(reverse("management_portal:account_approval", args=[customer.pk, "verify_mobile"]))

        self.assertRedirects(response, reverse("management_portal:approvals"))
        customer.refresh_from_db()
        self.assertIsNotNone(customer.mobile_verified_at)
        self.assertTrue(customer.email_verified)
        self.assertTrue(OperationalAudit.objects.filter(action="account_verify_mobile", target_id=str(customer.pk)).exists())
        self.assertEqual(
            ManagementNotification.objects.get(source_key=f"mobile-verification:{customer.pk}").status,
            "resolved",
        )

    def test_payment_approval_grants_access_once_and_records_audit(self):
        root = User.objects.create_superuser(username="pay-root", email="pay-root@example.com", password="safe-password")
        customer = User.objects.create_user(username="buyer", email="buyer@example.com", password="safe-password", is_active=True)
        exam = Exam.objects.create(slug="management-test", title_fa="آزمون", title_en="Exam", description_fa="شرح", description_en="Description", language_mode="bilingual", price_irr=500000)
        order = Order.objects.create(user=customer, exam=exam, subtotal_irr=500000, amount_irr=500000, gateway="card_transfer", terms_version="v1", terms_accepted_at=timezone.now())
        payment = ManualPaymentSubmission.objects.create(order=order, payer_name="خریدار", reference_number="REF-MANAGEMENT-1", paid_at=timezone.now())
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:payment_review", args=[payment.pk, "approve"]), {"review_note": "رسید بررسی شد"})
        self.assertRedirects(response, reverse("management_portal:approvals"))
        payment.refresh_from_db(); order.refresh_from_db()
        self.assertEqual(payment.status, "approved")
        self.assertEqual(order.status, "paid")
        self.assertEqual(ExamEntitlement.objects.filter(order=order).count(), 1)
        self.assertTrue(OperationalAudit.objects.filter(action="payment_approve", target_id=str(payment.pk)).exists())
        notification = ManagementNotification.objects.get(source_key=f"payment:{payment.pk}")
        self.assertEqual(notification.status, "resolved")
        self.assertEqual(notification.resolved_by, root)

    @override_settings(
        PAYMENT_AUTO_APPROVE_SECONDS=180,
        WEB_PUSH_VAPID_PRIVATE_KEY="",
        MANAGEMENT_ALERT_SMS_RECIPIENTS=(),
    )
    def test_pending_card_transfer_is_auto_approved_after_three_minutes_with_audit_notification(self):
        root = User.objects.create_superuser(
            username="auto-pay-root", email="auto-pay-root@example.com", password="safe-password",
        )
        customer = User.objects.create_user(
            username="auto-buyer", email="auto-buyer@example.com", password="safe-password", is_active=True,
        )
        exam = Exam.objects.create(
            slug="auto-payment", title_fa="آزمون خودکار", title_en="Auto payment",
            description_fa="", description_en="", language_mode="bilingual", price_irr=1_200_000,
        )
        order = Order.objects.create(
            user=customer, exam=exam, subtotal_irr=1_200_000, amount_irr=1_200_000,
            gateway="card_transfer", terms_version="2026-08", terms_accepted_at=timezone.now(),
        )
        payment = ManualPaymentSubmission.objects.create(
            order=order, payer_name="مشتری آزمایشی", reference_number="AUTO-180-TEST", paid_at=timezone.now(),
        )
        ManualPaymentSubmission.objects.filter(pk=payment.pk).update(
            updated_at=timezone.now() - timedelta(seconds=181),
        )

        result = process_notifications(now=timezone.now())

        payment.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(result["auto_approved"], 1)
        self.assertEqual(payment.status, "approved")
        self.assertIsNone(payment.reviewed_by)
        self.assertIn("تأیید خودکار سیستم", payment.review_note)
        self.assertEqual(order.status, "paid")
        self.assertEqual(ExamEntitlement.objects.filter(order=order).count(), 1)
        transaction_row = PaymentTransaction.objects.get(order=order)
        self.assertTrue(transaction_row.raw_response["automatic_review"])
        self.assertEqual(
            ManagementNotification.objects.get(source_key=f"payment:{payment.pk}").status,
            "resolved",
        )
        notification = ManagementNotification.objects.get(source_key=f"payment-auto-approved:{payment.pk}")
        self.assertEqual(notification.title, "پرداخت توسط سیستم تأیید شد")
        self.assertTrue(NotificationReceipt.objects.filter(notification=notification, user=root).exists())

        repeated = process_notifications(now=timezone.now() + timedelta(minutes=1))
        self.assertEqual(repeated["auto_approved"], 0)
        self.assertEqual(ExamEntitlement.objects.filter(order=order).count(), 1)

    @override_settings(PAYMENT_AUTO_APPROVE_SECONDS=180, WEB_PUSH_VAPID_PRIVATE_KEY="")
    def test_pending_card_transfer_remains_pending_before_three_minutes(self):
        customer = User.objects.create_user(
            username="early-buyer", email="early-buyer@example.com", password="safe-password", is_active=True,
        )
        exam = Exam.objects.create(
            slug="early-payment", title_fa="آزمون", title_en="Exam",
            description_fa="", description_en="", language_mode="bilingual", price_irr=100_000,
        )
        order = Order.objects.create(
            user=customer, exam=exam, subtotal_irr=100_000, amount_irr=100_000,
            gateway="card_transfer", terms_version="2026-08", terms_accepted_at=timezone.now(),
        )
        payment = ManualPaymentSubmission.objects.create(
            order=order, payer_name="خریدار", reference_number="BEFORE-180", paid_at=timezone.now(),
        )
        ManualPaymentSubmission.objects.filter(pk=payment.pk).update(
            updated_at=timezone.now() - timedelta(seconds=179),
        )

        result = process_notifications(now=timezone.now())

        payment.refresh_from_db()
        self.assertEqual(result["auto_approved"], 0)
        self.assertEqual(payment.status, "pending")
        self.assertFalse(ExamEntitlement.objects.filter(order=order).exists())

    @override_settings(PAYMENT_AUTO_APPROVE_SECONDS=180, WEB_PUSH_VAPID_PRIVATE_KEY="")
    def test_resubmitted_receipt_gets_a_fresh_three_minute_review_window(self):
        customer = User.objects.create_user(
            username="resubmit-buyer", email="resubmit-buyer@example.com", password="safe-password", is_active=True,
        )
        exam = Exam.objects.create(
            slug="resubmit-payment", title_fa="آزمون", title_en="Exam",
            description_fa="", description_en="", language_mode="bilingual", price_irr=100_000,
        )
        order = Order.objects.create(
            user=customer, exam=exam, subtotal_irr=100_000, amount_irr=100_000,
            gateway="card_transfer", terms_version="2026-08", terms_accepted_at=timezone.now(),
        )
        payment = ManualPaymentSubmission.objects.create(
            order=order, payer_name="خریدار", reference_number="RESUBMIT-180",
            paid_at=timezone.now(), status="rejected",
        )
        ManualPaymentSubmission.objects.filter(pk=payment.pk).update(
            updated_at=timezone.now() - timedelta(days=1),
        )
        payment.refresh_from_db()
        payment.status = "pending"
        payment.save()
        resubmitted_at = payment.updated_at

        early = process_notifications(now=resubmitted_at + timedelta(seconds=179))
        payment.refresh_from_db()
        self.assertEqual(early["auto_approved"], 0)
        self.assertEqual(payment.status, "pending")

        due = process_notifications(now=resubmitted_at + timedelta(seconds=181))
        payment.refresh_from_db()
        self.assertEqual(due["auto_approved"], 1)
        self.assertEqual(payment.status, "approved")

    def test_payment_approval_queue_shows_customer_and_transfer_details(self):
        root = User.objects.create_superuser(username="payment-details-root", email="payment-details@example.com", password="safe-password")
        customer = User.objects.create_user(
            username="payment-details-customer", email="buyer-details@example.com", mobile="98912009991",
            first_name="مینا", last_name="رضایی", password="safe-password", is_active=True,
        )
        exam = Exam.objects.create(slug="payment-details-exam", title_fa="آزمون پرداخت", title_en="Payment exam", description_fa="", description_en="", language_mode="bilingual", price_irr=100000)
        order = Order.objects.create(user=customer, exam=exam, amount_irr=100000)
        payment = ManualPaymentSubmission.objects.create(
            order=order, payer_name="مینا رضایی", reference_number="DETAILS-REF-1", paid_at=timezone.now(), note="واریز از حساب شرکت",
        )
        self.client.force_login(root)

        response = self.client.get(reverse("management_portal:approvals"))

        self.assertContains(response, "مشخصات کامل سفارش و واریز")
        self.assertContains(response, "buyer-details@example.com")
        self.assertContains(response, "98912009991")
        self.assertContains(response, str(order.pk))
        self.assertContains(response, "واریز از حساب شرکت")
        self.assertContains(response, f"review-note-{payment.pk}")

    @override_settings(PAYMENT_REVIEW_SLA_SECONDS=1800, WEB_PUSH_VAPID_PRIVATE_KEY="")
    def test_overdue_payment_creates_one_sla_alert_before_push_is_configured(self):
        customer = User.objects.create_user(username="sla-buyer", email="sla-buyer@example.com", password="safe-password", is_active=True)
        exam = Exam.objects.create(slug="sla-payment", title_fa="آزمون", title_en="Exam", description_fa="", description_en="", language_mode="bilingual", price_irr=100000)
        order = Order.objects.create(user=customer, exam=exam, amount_irr=100000)
        payment = ManualPaymentSubmission.objects.create(order=order, payer_name="خریدار", reference_number="SLA-PAYMENT-1", paid_at=timezone.now())
        ManualPaymentSubmission.objects.filter(pk=payment.pk).update(updated_at=timezone.now() - timedelta(minutes=31))
        process_notifications(now=timezone.now())
        self.assertTrue(ManagementNotification.objects.filter(source_key=f"sla:payment:{payment.pk}", category="payments").exists())
        process_notifications(now=timezone.now())
        self.assertEqual(ManagementNotification.objects.filter(source_key=f"sla:payment:{payment.pk}").count(), 1)

    @override_settings(
        SUPPORT_FIRST_RESPONSE_SLA_SECONDS=60,
        SALES_FOLLOW_UP_SLA_SECONDS=60,
        WEB_PUSH_VAPID_PRIVATE_KEY="",
        MANAGEMENT_ALERT_SMS_RECIPIENTS=(),
    )
    def test_payment_automation_keeps_support_and_sales_sla_alerts_active(self):
        customer = User.objects.create_user(
            username="sla-coverage", email="sla-coverage@example.com", password="safe-password", is_active=True,
        )
        ticket = SupportTicket.objects.create(
            user=customer, category="technical", subject="درخواست قدیمی", message="نیازمند بررسی",
        )
        lead = Lead.objects.create(
            name="مشتری SLA", email_or_telegram="sla-lead@example.com", phone="09120000000",
            message="پیگیری درخواست", privacy_accepted_at=timezone.now(),
        )
        SupportTicket.objects.filter(pk=ticket.pk).update(created_at=timezone.now() - timedelta(seconds=61))
        Lead.objects.filter(pk=lead.pk).update(created_at=timezone.now() - timedelta(seconds=61))

        process_notifications(now=timezone.now())

        self.assertTrue(ManagementNotification.objects.filter(source_key=f"sla:support:{ticket.pk}").exists())
        self.assertTrue(ManagementNotification.objects.filter(source_key=f"sla:lead:{lead.pk}").exists())

    def test_support_staff_can_update_ticket_without_admin(self):
        staff = User.objects.create_user(username="support", email="support@example.com", password="safe-password", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_supportticket"), Permission.objects.get(codename="change_supportticket"))
        customer = User.objects.create_user(username="support-customer", email="support-customer@example.com", password="safe-password", is_active=True)
        ticket = SupportTicket.objects.create(user=customer, category="technical", subject="مشکل ورود", message="صفحه ورود باز نمی‌شود")
        self.client.force_login(staff)
        listing = self.client.get(reverse("management_portal:assessment_support"))
        self.assertContains(listing, "مشکل ورود")
        self.assertNotContains(listing, 'href="/admin/')
        response = self.client.post(reverse("management_portal:ticket_status", args=[ticket.pk]), {"status": "in_review"})
        self.assertRedirects(response, reverse("management_portal:assessment_support"))
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, "in_review")
        self.assertTrue(OperationalAudit.objects.filter(action="ticket_status", target_id=str(ticket.pk)).exists())

    def test_content_staff_can_toggle_service_without_customer_access(self):
        staff = User.objects.create_user(username="content", email="content@example.com", password="safe-password", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_service"), Permission.objects.get(codename="change_service"))
        service = Service.objects.create(title_fa="خدمت آزمایشی", title_en="Test service", slug="content-test-service", short_description_fa="خلاصه", short_description_en="Summary", is_active=False)
        self.client.force_login(staff)
        page = self.client.get(reverse("management_portal:content_center"))
        self.assertContains(page, "خدمت آزمایشی")
        self.assertNotContains(page, "waiting@example.com")
        response = self.client.post(reverse("management_portal:content_toggle", args=["service", service.pk]), {"enabled": "1"})
        self.assertRedirects(response, reverse("management_portal:content_center"))
        service.refresh_from_db()
        self.assertTrue(service.is_active)
        self.assertTrue(OperationalAudit.objects.filter(action="content_state", target_type="service", target_id=str(service.pk)).exists())

    def test_superuser_sees_dashboard_shell(self):
        user = User.objects.create_superuser(username="root", email="root@example.com", password="safe-password")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertContains(response, "مرکز مدیریت")
        self.assertContains(response, "مرکز عملیات")

    def test_management_shell_uses_five_destination_navigation_without_a_mobile_hamburger(self):
        user = User.objects.create_superuser(username="root-shell", email="root-shell@example.com", password="safe-password")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertContains(response, "فرم‌ها و آزمون‌ها")
        self.assertContains(response, "قراردادها")
        self.assertContains(response, 'aria-controls="management-more-panel"', count=2)
        self.assertContains(response, "core/icons/ui-sprite.svg#home")
        self.assertNotContains(response, 'class="m-menu"')

    def test_content_staff_can_reach_the_permitted_content_center_from_more_tools(self):
        staff = User.objects.create_user(username="content-shell", email="content-shell@example.com", password="safe-password", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_service"))
        self.client.force_login(staff)
        response = self.client.get(self.url)
        self.assertContains(response, f'href="{reverse("management_portal:content_center")}"')
        self.assertContains(response, "محتوا و سایت")
        self.assertNotContains(response, "تیم و دسترسی")

    def test_new_dashboard_is_language_scoped_and_does_not_link_to_django_admin(self):
        root = User.objects.create_superuser(username="root-lang", email="root-lang@example.com", password="safe-password")
        self.client.force_login(root)
        fa = self.client.get("/fa/management/")
        self.assertContains(fa, "خانه مدیریت")
        self.assertNotContains(fa, 'href="/admin/')
        en = self.client.get("/en/management/")
        self.assertContains(en, "What needs your decision today?")
        self.assertContains(en, "Team &amp; access", html=True)
        self.assertContains(en, "Business management")
        self.assertContains(en, "management.css?v=15")
        self.assertNotContains(en, 'href="/admin/')

        management_css = (Path(__file__).resolve().parent / "static" / "management_portal" / "v2" / "management.css").read_text(encoding="utf-8")
        self.assertIn('html[lang="en"]{--font-family-base:var(--font-family-latin)}', management_css)

    def test_management_workspaces_keep_operational_labels_language_scoped(self):
        root = User.objects.create_superuser(username="language-root", email="language-root@example.com", password="safe-password")
        case = CustomerCase.objects.create(
            kind="lead", customer_name="Acme", contact_name="Alex",
            stage="discovery", priority="urgent",
        )
        CaseActivity.objects.create(case=case, kind="system", title="Imported", body="")
        SystemLog.objects.create(level="error", category="server", message_fa="پیام داخلی فارسی", detail="TypeError: example")
        self.client.force_login(root)

        fa_workspace = self.client.get("/fa/management/crm/")
        self.assertContains(fa_workspace, "عملیات مشتری آرویون")
        self.assertNotContains(fa_workspace, "RVION CUSTOMER OPERATIONS")
        fa_detail = self.client.get(f"/fa/management/crm/cases/{case.pk}/")
        self.assertContains(fa_detail, ">خط زمانی<", html=False)
        self.assertNotContains(fa_detail, ">TIMELINE<", html=False)

        en_workspace = self.client.get("/en/management/crm/")
        self.assertContains(en_workspace, "RVION CUSTOMER OPERATIONS")
        self.assertContains(en_workspace, ">Enquiry<", html=False)
        self.assertContains(en_workspace, ">Discovery<", html=False)
        self.assertContains(en_workspace, ">Urgent<", html=False)
        self.assertNotContains(en_workspace, ">همکاری<", html=False)
        en_detail = self.client.get(f"/en/management/crm/cases/{case.pk}/")
        self.assertContains(en_detail, ">TIMELINE<", html=False)
        self.assertContains(en_detail, "System")
        self.assertNotContains(en_detail, ">خط زمانی<", html=False)

        en_logs = self.client.get("/en/management/system-log/")
        self.assertContains(en_logs, "SYSTEM HEALTH")
        self.assertContains(en_logs, "TypeError: example")
        self.assertNotContains(en_logs, "پیام داخلی فارسی")

    def test_management_messages_preserve_severity_and_live_region_semantics(self):
        root = User.objects.create_superuser(username="message-root", email="message-root@example.com", password="safe-password")
        customer = User.objects.create_user(username="pending-message", email="pending-message@example.com", password="safe-password", is_active=False)
        self.client.force_login(root)

        error_response = self.client.post(
            reverse("management_portal:account_approval", args=[customer.pk, "verify_mobile"]) + "?lang=en",
            follow=True,
        )
        self.assertContains(error_response, 'class="m-message error"', html=False)
        self.assertContains(error_response, 'role="alert" aria-live="assertive"', html=False)

        staff = User.objects.create_user(username="message-staff", email="message-staff@example.com", password="safe-password", is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename="view_supportticket"), Permission.objects.get(codename="change_supportticket"))
        ticket = SupportTicket.objects.create(user=customer, category="technical", subject="Test", message="Example")
        self.client.force_login(staff)
        success_response = self.client.post(
            reverse("management_portal:ticket_status", args=[ticket.pk]) + "?lang=en",
            {"status": "in_review"},
            follow=True,
        )
        self.assertContains(success_response, 'class="m-message success"', html=False)
        self.assertContains(success_response, 'role="status" aria-live="polite"', html=False)

    def test_legacy_management_redirects_to_persian_workspace(self):
        response = self.client.get("/management/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/fa/management/")

    def test_only_superuser_can_manage_staff(self):
        staff = User.objects.create_user(username="staff", email="staff@example.com", password="safe-password", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("management_portal:staff_list")).status_code, 403)

    def test_superuser_creates_least_privilege_staff_with_selected_roles(self):
        root = User.objects.create_superuser(username="root2", email="root2@example.com", password="safe-password")
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:staff_create"), {
            "first_name": "سارا", "last_name": "فروش", "email": "sales2@example.com",
            "password": "Safe-Rvion-Password-932!", "roles": ["sales", "analytics"],
        })
        self.assertRedirects(response, reverse("management_portal:staff_list"))
        member = User.objects.get(email="sales2@example.com")
        self.assertTrue(member.is_staff)
        self.assertFalse(member.is_superuser)
        self.assertTrue(member.groups.filter(name=group_name("sales")).exists())
        self.assertTrue(member.groups.filter(name=group_name("analytics")).exists())
        self.assertFalse(member.has_perm("accounts.change_user"))
        audit = StaffAccessAudit.objects.get(target=member)
        self.assertEqual(audit.actor, root)
        self.assertEqual(audit.action, "created")
        self.assertEqual(set(audit.roles), {"sales", "analytics"})

    def test_superuser_cannot_edit_another_superuser_roles(self):
        root = User.objects.create_superuser(username="root3", email="root3@example.com", password="safe-password")
        other = User.objects.create_superuser(username="root4", email="root4@example.com", password="safe-password")
        self.client.force_login(root)
        self.assertEqual(self.client.get(reverse("management_portal:staff_edit", args=[other.pk])).status_code, 403)

    def test_new_customer_creates_account_notification(self):
        customer = User.objects.create_user(
            username="new-customer", email="new-customer@example.com",
            password="safe-password", mobile_verified_at=timezone.now(),
        )
        notification = ManagementNotification.objects.get(source_key=f"user:{customer.pk}")
        self.assertEqual(notification.category, "accounts")
        self.assertEqual(notification.status, "unread")

    def test_incomplete_registration_does_not_create_stale_account_notification(self):
        customer = User.objects.create_user(
            username="pending-customer", email="pending-customer@example.com",
            password="safe-password", is_active=False, mobile="989120000099",
        )
        self.assertFalse(
            ManagementNotification.objects.filter(source_key=f"user:{customer.pk}").exists(),
        )

        customer.mobile_verified_at = timezone.now()
        customer.is_active = True
        customer.save(update_fields=["mobile_verified_at", "is_active"])

        self.assertTrue(
            ManagementNotification.objects.filter(source_key=f"user:{customer.pk}").exists(),
        )

    def test_notifications_are_filtered_by_role_and_can_be_resolved(self):
        root = User.objects.create_superuser(username="notify-root", email="notify-root@example.com", password="safe-password")
        sales = User.objects.create_user(username="notify-sales", email="notify-sales@example.com", password="safe-password", is_staff=True)
        from accounts.staff_roles import sync_staff_role_groups
        sales.groups.add(sync_staff_role_groups()["sales"])
        sales_item = ManagementNotification.objects.create(category="sales", title="فروش", target_url="/admin/", role="sales", source_key="test:sales")
        ManagementNotification.objects.create(category="payments", title="مالی", target_url="/admin/", role="assessments", source_key="test:payments")
        self.client.force_login(sales)
        response = self.client.get(reverse("management_portal:notification_list"))
        self.assertContains(response, "فروش")
        self.assertNotContains(response, "مالی")
        update = self.client.post(reverse("management_portal:notification_status", args=[sales_item.pk, "resolved"]))
        self.assertRedirects(update, reverse("management_portal:notification_list"))
        sales_item.refresh_from_db()
        self.assertEqual(sales_item.resolved_by, sales)
        self.client.force_login(root)
        self.assertContains(self.client.get(reverse("management_portal:notification_list")), "مالی")

    @override_settings(WEB_PUSH_VAPID_PRIVATE_KEY="test-key", MANAGEMENT_ALERT_SMS_RECIPIENTS=["989120373271"])
    @patch("management_portal.notifications.send_sms")
    @patch("management_portal.notifications._send_user_push", return_value="")
    def test_new_payment_pushes_immediately_and_sends_only_one_urgent_sms(self, mocked_push, mocked_sms):
        root = User.objects.create_superuser(username="alert-root", email="alert-root@example.com", password="safe-password")
        item = ManagementNotification.objects.create(category="payments", title="رسید جدید", description="REF-1", target_url="/fa/management/approvals/", role="", source_key="alert:payment")
        NotificationReceipt.objects.create(user=root, notification=item)
        first = process_notifications()
        second = process_notifications()
        self.assertEqual(first["push"], 1)
        self.assertEqual(first["sms"], 1)
        self.assertEqual(second["sms"], 0)
        self.assertEqual(mocked_sms.call_count, 1)
        self.assertGreaterEqual(mocked_push.call_count, 1)

    @override_settings(WEB_PUSH_VAPID_PRIVATE_KEY="test-key", MANAGEMENT_REMINDER_SECONDS=3600)
    @patch("management_portal.notifications._send_user_push", return_value="")
    def test_seen_notifications_do_not_send_hourly_reminder_but_new_items_do(self, mocked_push):
        root = User.objects.create_superuser(username="reminder-root", email="reminder-root@example.com", password="safe-password")
        old = ManagementNotification.objects.create(category="sales", title="درخواست", target_url="/fa/management/requests/", role="", source_key="alert:old")
        receipt = NotificationReceipt.objects.create(user=root, notification=old, push_sent_at=timezone.now()-timedelta(hours=2))
        self.client.force_login(root)
        self.client.get(reverse("management_portal:notification_list"))
        receipt.refresh_from_db()
        self.assertIsNotNone(receipt.seen_at)
        result = process_notifications(now=timezone.now())
        self.assertEqual(result["reminders"], 0)
        newer = ManagementNotification.objects.create(category="sales", title="درخواست تازه", target_url="/fa/management/requests/", role="", source_key="alert:new")
        new_receipt = NotificationReceipt.objects.create(user=root, notification=newer, push_sent_at=timezone.now()-timedelta(hours=2))
        ManagementNotification.objects.filter(pk=newer.pk).update(created_at=timezone.now()-timedelta(hours=2))
        result = process_notifications(now=timezone.now())
        self.assertEqual(result["reminders"], 1)
        new_receipt.refresh_from_db()
        self.assertIsNotNone(new_receipt.last_reminded_at)

    def test_staff_can_register_push_subscription(self):
        root = User.objects.create_superuser(username="push-root", email="push-root@example.com", password="safe-password")
        self.client.force_login(root)
        with override_settings(
            WEB_PUSH_VAPID_PUBLIC_KEY="public-key",
            WEB_PUSH_ALLOWED_HOST_SUFFIXES=("push.example",),
        ):
            response = self.client.post(reverse("management_portal:push_subscribe"), data='{"endpoint":"https://push.example/sub","keys":{"p256dh":"key","auth":"auth"}}', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PushSubscription.objects.filter(user=root, is_active=True).exists())

    @override_settings(WEB_PUSH_VAPID_PUBLIC_KEY="public-key")
    def test_push_subscription_rejects_untrusted_or_internal_endpoint(self):
        root = User.objects.create_superuser(
            username="push-security-root", email="push-security-root@example.com",
            password="safe-password",
        )
        self.client.force_login(root)
        for endpoint in ("http://fcm.googleapis.com/sub", "https://127.0.0.1/sub", "https://attacker.example/sub"):
            response = self.client.post(
                reverse("management_portal:push_subscribe"),
                data=json.dumps({"endpoint": endpoint, "keys": {"p256dh": "key", "auth": "auth"}}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)
        self.assertFalse(PushSubscription.objects.filter(user=root).exists())

    def test_opening_push_marks_only_that_notification_seen(self):
        root = User.objects.create_superuser(username="open-root", email="open-root@example.com", password="safe-password")
        first = ManagementNotification.objects.create(category="sales", title="اول", target_url=reverse("management_portal:request_list"), role="", source_key="open:first")
        second = ManagementNotification.objects.create(category="sales", title="دوم", target_url=reverse("management_portal:request_list"), role="", source_key="open:second")
        first_receipt = NotificationReceipt.objects.create(user=root, notification=first)
        second_receipt = NotificationReceipt.objects.create(user=root, notification=second)
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:notification_open", args=[first.pk]))
        self.assertRedirects(response, reverse("management_portal:request_list"))
        first_receipt.refresh_from_db(); second_receipt.refresh_from_db()
        self.assertIsNotNone(first_receipt.seen_at)
        self.assertIsNone(second_receipt.seen_at)

    def test_legacy_notification_opens_the_matching_management_path(self):
        root = User.objects.create_superuser(username="legacy-open", email="legacy-open@example.com", password="safe-password")
        item = ManagementNotification.objects.create(category="payments", title="رسید", target_url="/admin/assessments/manualpaymentsubmission/", role="", source_key="legacy:payment")
        NotificationReceipt.objects.create(user=root, notification=item)
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:notification_open", args=[item.pk]))
        self.assertRedirects(response, reverse("management_portal:approvals"))
        page = self.client.get(reverse("management_portal:notification_list"))
        self.assertEqual(page.status_code, 200)

    def test_notification_redirects_cannot_leave_the_site(self):
        root = User.objects.create_superuser(
            username="redirect-root", email="redirect-root@example.com",
            password="safe-password",
        )
        item = ManagementNotification.objects.create(
            category="sales", title="ناامن", target_url="https://attacker.example/phish",
            role="", source_key="redirect:external",
        )
        self.client.force_login(root)

        opened = self.client.get(reverse("management_portal:notification_open", args=[item.pk]))
        self.assertRedirects(opened, reverse("management_portal:notification_list"))
        claimed = self.client.post(
            reverse("management_portal:notification_claim", args=[item.pk]),
            {"next": "https://attacker.example/phish"},
        )
        self.assertRedirects(claimed, reverse("management_portal:notification_list"))

    def test_sms_page_is_restricted_to_superuser(self):
        staff = User.objects.create_user(username="sms-staff", email="sms-staff@example.com", password="safe-password", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("management_portal:sms_send")).status_code, 403)

    @patch("management_portal.views.send_sms")
    def test_superuser_can_send_unique_normalized_sms_batch(self, mocked_send):
        mocked_send.return_value = SMSResult(provider="test", reference="ref-1")
        root = User.objects.create_superuser(username="sms-root", email="sms-root@example.com", password="safe-password")
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:sms_send"), {
            "recipients": "09120373271\n+98 912 037 3271\n۰۹۱۲۱۱۱۲۲۳۳",
            "message": "پیام آزمایشی آرویون",
            "confirm": "on",
        })
        self.assertRedirects(response, reverse("management_portal:sms_send"))
        self.assertEqual(mocked_send.call_count, 2)
        self.assertEqual(SMSDispatch.objects.filter(status="sent").count(), 2)
        self.assertSetEqual(set(SMSDispatch.objects.values_list("recipient", flat=True)), {"989120373271", "989121112233"})

    @patch("management_portal.views.send_sms")
    def test_invalid_batch_does_not_send_any_sms(self, mocked_send):
        root = User.objects.create_superuser(username="sms-root-invalid", email="sms-root-invalid@example.com", password="safe-password")
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:sms_send"), {
            "recipients": "09120373271\n02112345678", "message": "سلام", "confirm": "on",
        })
        self.assertEqual(response.status_code, 200)
        mocked_send.assert_not_called()
        self.assertContains(response, "شماره نامعتبر")

    @patch("management_portal.views.send_sms")
    def test_superuser_can_send_live_registered_segment_with_campaign_audit(self, mocked_send):
        mocked_send.return_value = SMSResult(provider="test", reference="segment-ref")
        root = User.objects.create_superuser(username="segment-root", email="segment-root@example.com", password="safe-password")
        User.objects.create_user(username="segment-a", email="segment-a@example.com", mobile="09121110001", password="safe-password", is_active=True)
        User.objects.create_user(username="segment-b", email="segment-b@example.com", mobile="09121110002", password="safe-password", is_active=True)
        self.client.force_login(root)

        preview = self.client.get(reverse("management_portal:sms_send") + "?audience=registered")
        self.assertContains(preview, "عضو بدون سفارش")
        self.assertContains(preview, "989121110001")
        response = self.client.post(reverse("management_portal:sms_send"), {
            "audience": "registered", "expected_count": "2", "recipients": "",
            "message": "پیگیری ثبت سفارش آرویون", "confirm": "on",
        })

        self.assertRedirects(response, reverse("management_portal:sms_send"))
        self.assertEqual(mocked_send.call_count, 2)
        campaign = SMSCampaign.objects.get()
        self.assertEqual((campaign.recipient_count, campaign.sent_count, campaign.failed_count), (2, 2, 0))
        self.assertEqual(campaign.dispatches.count(), 2)
        self.assertTrue(OperationalAudit.objects.filter(action="sms_campaign_sent", target_id=str(campaign.pk)).exists())

    @patch("management_portal.views.send_sms")
    def test_changed_segment_requires_a_fresh_preview(self, mocked_send):
        root = User.objects.create_superuser(username="segment-race-root", email="segment-race-root@example.com", password="safe-password")
        User.objects.create_user(username="segment-race", email="segment-race@example.com", mobile="09121110003", password="safe-password", is_active=True)
        self.client.force_login(root)

        response = self.client.post(reverse("management_portal:sms_send"), {
            "audience": "registered", "expected_count": "0", "recipients": "",
            "message": "نباید ارسال شود", "confirm": "on",
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "اعضای گروه تغییر کرده‌اند")
        mocked_send.assert_not_called()
        self.assertFalse(SMSCampaign.objects.exists())

    def test_prepared_sms_templates_are_seeded(self):
        self.assertEqual(SMSMessageTemplate.objects.filter(is_active=True).count(), 5)
        self.assertTrue(SMSMessageTemplate.objects.filter(audience="ready", body_fa__contains="rvionai.com").exists())

    def test_payment_and_ticket_are_saved_in_the_customer_timeline(self):
        user = User.objects.create_user(username="timeline-user", email="timeline@example.com", mobile="09120003344", password="safe-password")
        customer = Customer.objects.create(name="مشتری آزمون", kind="person", phone=user.mobile, email=user.email)
        CustomerContact.objects.create(customer=customer, name="مشتری آزمون", phone=user.mobile, email=user.email, user=user, is_primary=True)
        exam = Exam.objects.create(slug="timeline-exam", title_fa="آزمون", title_en="Exam", description_fa="", description_en="", language_mode="bilingual", price_irr=100000)
        order = Order.objects.create(user=user, customer=customer, exam=exam, amount_irr=100000)
        payment = ManualPaymentSubmission.objects.create(order=order, payer_name="مشتری آزمون", reference_number="TIMELINE-REF-1", paid_at=timezone.now())
        ticket = SupportTicket.objects.create(user=user, order=order, category="technical", subject="اشکال ورود", message="نمونه پیام")
        case = CustomerCase.objects.get(customer=customer)
        self.assertTrue(case.documents.filter(object_id=payment.pk, kind="payment").exists())
        self.assertTrue(case.documents.filter(object_id=ticket.pk, kind="attachment").exists())
        self.assertTrue(CaseActivity.objects.filter(case=case, title="رسید پرداخت ارسال شد").exists())
        self.assertTrue(CaseActivity.objects.filter(case=case, title="تیکت پشتیبانی جدید").exists())

    def test_operations_dashboard_displays_operational_inbox(self):
        root = User.objects.create_superuser(username="inbox-root", email="inbox-root@example.com", password="safe-password")
        notification = ManagementNotification.objects.create(category="payments", title="رسید پرداخت جدید", description="REF-INBOX", target_url=reverse("management_portal:approvals"), role="", source_key="inbox:payment")
        NotificationReceipt.objects.create(user=root, notification=notification)
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:dashboard"))
        self.assertContains(response, "صندوق عملیاتی")
        self.assertContains(response, "رسید پرداخت جدید")

    def test_notification_inbox_groups_work_and_staff_can_claim_an_item(self):
        root = User.objects.create_superuser(username="queue-root", email="queue@example.com", password="safe-password")
        payment = ManagementNotification.objects.create(category="payments", title="رسید فوری", target_url=reverse("management_portal:approvals"), role="", source_key="queue:payment", due_at=timezone.now() + timedelta(minutes=20))
        today = ManagementNotification.objects.create(category="sales", title="پیگیری امروز", target_url=reverse("management_portal:request_list"), role="", source_key="queue:today", due_at=timezone.now() + timedelta(hours=2))
        later = ManagementNotification.objects.create(category="sales", title="پیگیری بعدی", target_url=reverse("management_portal:request_list"), role="", source_key="queue:later", due_at=timezone.now() + timedelta(days=2))
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:notification_list"))
        self.assertContains(response, "اکنون رسیدگی کنید")
        self.assertContains(response, "پیگیری امروز")
        self.assertContains(response, "پیگیری بعدی")
        claimed = self.client.post(reverse("management_portal:notification_claim", args=[today.pk]))
        self.assertRedirects(claimed, reverse("management_portal:notification_list"))
        today.refresh_from_db()
        self.assertEqual(today.owner, root)
        self.assertEqual(today.status, "read")
        self.assertTrue(OperationalAudit.objects.filter(action="notification_claimed", target_id=str(today.pk)).exists())
        self.assertEqual(payment.category, "payments")
        self.assertEqual(later.owner, None)

    def test_notification_cards_only_refer_to_work_while_legacy_actions_keep_api_fallback(self):
        root = User.objects.create_superuser(username="async-notify-root", email="async-notify@example.com", password="safe-password")
        claimed_item = ManagementNotification.objects.create(category="sales", title="پیگیری سریع", target_url=reverse("management_portal:request_list"), role="", source_key="async:claim")
        resolved_item = ManagementNotification.objects.create(category="payments", title="رسید آماده", target_url=reverse("management_portal:approvals"), role="", source_key="async:resolve")
        NotificationReceipt.objects.create(user=root, notification=claimed_item)
        NotificationReceipt.objects.create(user=root, notification=resolved_item)
        self.client.force_login(root)

        inbox = self.client.get(reverse("management_portal:notification_list"))
        self.assertNotContains(inbox, 'data-notification-action="claim"')
        self.assertNotContains(inbox, 'data-notification-action="resolved"')
        self.assertContains(inbox, "رفتن به محل انجام کار")
        self.assertContains(inbox, "data-notification-queue")

        claimed = self.client.post(
            reverse("management_portal:notification_claim", args=[claimed_item.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(claimed.status_code, 200)
        self.assertEqual(claimed.json()["action"], "claim")
        self.assertEqual(claimed.json()["status"], "read")
        self.assertEqual(claimed.json()["owner"], root.email)
        claimed_item.refresh_from_db()
        self.assertEqual(claimed_item.owner, root)

        resolved = self.client.post(
            reverse("management_portal:notification_status", args=[resolved_item.pk, "resolved"]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(resolved.status_code, 200)
        self.assertEqual(resolved.json()["action"], "resolved")
        resolved_item.refresh_from_db()
        self.assertEqual(resolved_item.status, "resolved")

        fallback_item = ManagementNotification.objects.create(category="sales", title="فرآیند فالبک", target_url=reverse("management_portal:request_list"), role="", source_key="async:fallback")
        fallback = self.client.post(reverse("management_portal:notification_status", args=[fallback_item.pk, "read"]))
        self.assertRedirects(fallback, reverse("management_portal:notification_list"))

    def test_dashboard_shows_role_scoped_sla_cards(self):
        root = User.objects.create_superuser(username="sla-dashboard", email="sla-dashboard@example.com", password="safe-password")
        user = User.objects.create_user(username="sla-customer", email="sla-customer@example.com", password="safe-password")
        exam = Exam.objects.create(slug="sla-dashboard-exam", title_fa="آزمون SLA", title_en="SLA test", description_fa="", description_en="", language_mode="bilingual", price_irr=100000)
        order = Order.objects.create(user=user, exam=exam, amount_irr=100000)
        payment = ManualPaymentSubmission.objects.create(order=order, payer_name="مشتری", reference_number="SLA-DASH", paid_at=timezone.now())
        ManualPaymentSubmission.objects.filter(pk=payment.pk).update(updated_at=timezone.now() - timedelta(minutes=31))
        self.client.force_login(root)
        response = self.client.get(reverse("management_portal:dashboard"))
        self.assertContains(response, "مواردی که از SLA عبور کرده‌اند")
        self.assertContains(response, "تأیید خودکار معطل")
        self.assertContains(response, ">1<")
