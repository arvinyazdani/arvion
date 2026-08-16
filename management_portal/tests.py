from django.contrib.auth.models import Permission
from datetime import timedelta
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import User
from accounts.staff_roles import group_name
from crm_orders.models import CrmOrder, CrmSpecialistDiscovery
from assessments.models import Exam, ExamEntitlement, ManualPaymentSubmission, Order, SupportTicket
from contracts.models import ContractProposal
from management_portal.models import CaseTask, Customer, CustomerCase, CustomerContact, ManagementNotification, NotificationReceipt, OperationalAudit, PushSubscription, SMSDispatch, StaffAccessAudit
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
        self.assertContains(detail, "فرم تخصصی مشتری")
        case = CustomerCase.objects.get(source_object_id=order.pk, kind="crm")
        workspace = self.client.get(reverse("management_portal:crm_workspace"))
        self.assertContains(workspace, "سازمان آزمایشی")
        self.assertContains(self.client.get(reverse("management_portal:crm_case_detail", args=[case.pk])), case.code)
        self.client.post(reverse("management_portal:crm_task_create", args=[case.pk]), {"title": "تماس پیگیری", "priority": "high"})
        self.assertTrue(CaseTask.objects.filter(case=case, title="تماس پیگیری").exists())
        self.assertEqual(self.client.get(reverse("management_portal:crm_case_export", args=[case.pk])).status_code, 200)
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
        customer = User.objects.create_user(username="waiting", email="waiting@example.com", password="safe-password", is_active=False)
        self.client.force_login(root)
        response = self.client.post(reverse("management_portal:account_approval", args=[customer.pk, "approve"]))
        self.assertRedirects(response, reverse("management_portal:approvals"))
        customer.refresh_from_db()
        self.assertTrue(customer.is_active)
        self.assertTrue(customer.email_verified)
        self.assertTrue(OperationalAudit.objects.filter(action="account_approve", target_id=str(customer.pk)).exists())

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
        self.assertNotContains(en, 'href="/admin/')

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
        customer = User.objects.create_user(username="new-customer", email="new-customer@example.com", password="safe-password")
        notification = ManagementNotification.objects.get(source_key=f"user:{customer.pk}")
        self.assertEqual(notification.category, "accounts")
        self.assertEqual(notification.status, "unread")

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
        with override_settings(WEB_PUSH_VAPID_PUBLIC_KEY="public-key"):
            response = self.client.post(reverse("management_portal:push_subscribe"), data='{"endpoint":"https://push.example/sub","keys":{"p256dh":"key","auth":"auth"}}', content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PushSubscription.objects.filter(user=root, is_active=True).exists())

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
