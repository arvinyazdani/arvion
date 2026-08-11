from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from crm_orders.models import CrmOrder


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
