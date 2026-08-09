from django.contrib.auth.models import Group
from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .forms import CrmOrderForm
from .models import CrmOrder


def valid_payload():
    return {
        "organization_name": "سازمان نمونه", "industry": "توزیع و فروش", "organization_size": "51_200",
        "website": "https://example.com", "contact_name": "علی احمدی", "job_title": "مدیر تحول دیجیتال",
        "work_email": "ali@example.com", "phone": "۰۹۱۲۱۲۳۴۵۶۷",
        "primary_goals": ["sales", "service"], "departments": ["sales", "support", "management"],
        "crm_user_count": "31_100", "current_process": "اطلاعات مشتری بین فایل‌های اکسل و تماس‌های تیم توزیع شده است.",
        "main_pain_points": "پیگیری‌ها فراموش می‌شوند، گزارش دقیق نداریم و سابقه مشتری پراکنده است.",
        "success_metrics": "کاهش زمان پاسخ و افزایش نرخ تبدیل فرصت به قرارداد.",
        "required_capabilities": ["customer_360", "pipeline", "tasks", "reports"],
        "critical_workflows": "سرنخ وارد می‌شود، ارزیابی و تخصیص می‌گیرد، پیشنهاد صادر و سپس قرارداد ثبت می‌شود.",
        "reports_needed": "نرخ تبدیل، زمان پاسخ، ارزش pipeline و عملکرد کارشناسان.",
        "permission_requirements": "کارشناس فقط مشتریان خود و مدیر همه تیم را ببیند.",
        "current_tools": "Excel و نرم‌افزار حسابداری", "required_integrations": "وب‌سایت و حسابداری",
        "migration_sources": "سه فایل Excel و دفترچه مشتریان", "approximate_record_count": "25000",
        "hosting_preference": "unsure", "security_requirements": "ثبت تاریخچه تغییرات و دسترسی نقش‌محور.",
        "budget_range": "150_500", "expected_timeline": "2_4",
        "decision_process": "مدیرعامل و مدیر فروش پس از دریافت پیشنهاد فنی و مالی تصمیم می‌گیرند.",
        "additional_notes": "اجرای مرحله‌ای ترجیح داده می‌شود.", "privacy_accept": "on", "company_fax": "",
    }


class CrmOrderTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_wizard_is_separate_public_flow_with_accessible_steps(self):
        response = self.client.get(reverse("crm_orders:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ENTERPRISE CRM DISCOVERY")
        self.assertContains(response, 'data-crm-wizard', html=False)
        self.assertContains(response, 'aria-label="مراحل سفارش"')

    def test_valid_submission_persists_structured_discovery_and_emails_team(self):
        response = self.client.post(reverse("crm_orders:create"), valid_payload(), follow=True)
        order = CrmOrder.objects.get()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.tracking_code)
        self.assertEqual(order.primary_goals, ["sales", "service"])
        self.assertEqual(order.phone, "09121234567")
        self.assertIsNotNone(order.privacy_accepted_at)
        self.assertEqual(len(mail.outbox), 1)

    def test_short_architecture_answers_are_rejected_server_side(self):
        payload = valid_payload()
        payload["critical_workflows"] = "فروش"
        response = self.client.post(reverse("crm_orders:create"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "critical_workflows", "لطفاً حداقل ۲۰ کاراکتر توضیح دهید.")
        self.assertFalse(CrmOrder.objects.exists())

    def test_honeypot_rejects_bot_submission(self):
        payload = valid_payload()
        payload["company_fax"] = "spam"
        form = CrmOrderForm(payload)
        self.assertFalse(form.is_valid())
        self.assertIn("company_fax", form.errors)

    def test_sales_role_receives_crm_order_permissions(self):
        call_command("setup_staff_roles", verbosity=0)
        group = Group.objects.get(name="rvion_sales")
        self.assertTrue(group.permissions.filter(codename="view_crmorder").exists())
        self.assertTrue(group.permissions.filter(codename="change_crmorder").exists())
        self.assertFalse(group.permissions.filter(codename="delete_crmorder").exists())
