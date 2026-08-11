from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.staff_roles import group_name
from crm_orders.models import CrmOrder
from management_portal.models import StaffAccessAudit


class ManagementDashboardTests(TestCase):
    def setUp(self):
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

    def test_superuser_sees_dashboard_shell(self):
        user = User.objects.create_superuser(username="root", email="root@example.com", password="safe-password")
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertContains(response, "مرکز مدیریت")
        self.assertContains(response, "صندوق کار")

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
