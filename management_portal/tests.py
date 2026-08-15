from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone, translation

from accounts.models import User
from accounts.staff_roles import group_name
from crm_orders.models import CrmOrder
from management_portal.models import ManagementNotification, SMSDispatch, StaffAccessAudit
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

    def test_staff_only_sees_permitted_operational_data(self):
        user = User.objects.create_user(username="sales", email="sales@example.com", password="safe-password", is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename="view_crmorder"))
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "نیازسنجی CRM")
        self.assertNotContains(response, "پرداخت منتظر بررسی")
        self.assertNotContains(response, "حساب نیازمند تأیید")

    def test_sales_staff_can_manage_requests_without_django_admin_links(self):
        user = User.objects.create_user(username="sales-v2", email="sales-v2@example.com", password="safe-password", is_staff=True)
        user.user_permissions.add(Permission.objects.get(codename="view_crmorder"))
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

    def test_superuser_sees_dashboard_shell(self):
        user = User.objects.create_superuser(username="root", email="root@example.com", password="safe-password")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertContains(response, "مرکز مدیریت")
        self.assertContains(response, "صندوق کار")

    def test_new_dashboard_is_language_scoped_and_does_not_link_to_django_admin(self):
        root = User.objects.create_superuser(username="root-lang", email="root-lang@example.com", password="safe-password")
        self.client.force_login(root)
        fa = self.client.get("/fa/management/")
        self.assertContains(fa, "خانه مدیریت")
        self.assertNotContains(fa, 'href="/admin/')
        en = self.client.get("/en/management/")
        self.assertContains(en, "Today’s priorities")
        self.assertContains(en, "Team &amp; Access", html=True)
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
